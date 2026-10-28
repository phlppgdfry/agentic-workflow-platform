"""One checkpoint per tick, with bounded dependency retries and write approval."""
import json
from .models import Plan, RunRequest
from .planners import PermanentFailure, TransientFailure
from .store import Conflict, Store, canonical


class LocalTools:
    # Synthetic, tenant-scoped fixture records. Unknown customers fail closed.
    customers = {("demo", "C-001"): {"name": "Synthetic Example BV", "active": True},
                 ("demo", "C-002"): {"name": "Synthetic Closed BV", "active": False}}

    def execute(self, call, tenant, previous):
        if call.tool == "lookup_customer":
            customer = self.customers.get((tenant, call.arguments.customer_id))
            if not customer or not customer["active"]:
                raise PermanentFailure("customer_not_available")
            return {"customer_id": call.arguments.customer_id, **customer}
        if call.tool == "check_policy":
            return {"policy_id": "accounting-intake-v1", "human_approval_required": True,
                    "allowed_action": "create_mock_crm_case", "sensitive_data": "synthetic_only"}
        if call.tool == "prepare_case":
            if len(previous) != 2 or previous[1].get("policy_id") != "accounting-intake-v1":
                raise PermanentFailure("required_evidence_missing")
            return {"proposal": call.arguments.model_dump(), "policy_id": previous[1]["policy_id"]}
        raise PermanentFailure("tool_not_allowed")


class Engine:
    def __init__(self, store: Store, planner, tools=None, max_attempts=3, retry_base_seconds=2):
        self.store, self.planner = store, planner
        self.tools = tools or LocalTools()
        self.max_attempts, self.retry_base_seconds = max_attempts, retry_base_seconds

    def tick(self, run_id, tenant):
        claimed = self.store.claim(run_id, tenant)
        if not claimed:
            return self.store.get(run_id, tenant)
        token = claimed["lease_token"]
        try:
            if claimed["mode"] != self.planner.mode:
                raise PermanentFailure("planner_mode_changed_since_creation")
            if claimed["status"] == "queued":
                request = RunRequest.model_validate_json(claimed["request_json"])
                plan = self.planner.plan(request)
                plan.check_scope(request.customer_id)
                with self.store.transaction() as db:
                    self.store.fenced(db, run_id, tenant, token)
                    self.store.release(db, run_id, plan_json=plan.model_dump_json(), status="running",
                                       attempts=0, next_attempt_at=0, last_error=None)
                    self.store.event(db, run_id, "planner", "plan_validated", {"mode": self.planner.mode, "steps": 3})
            elif claimed["status"] == "running":
                plan = Plan.model_validate_json(claimed["plan_json"])
                index = claimed["cursor"]
                with self.store.transaction() as db:
                    self.store.fenced(db, run_id, tenant, token)
                    receipts = [json.loads(r["result_json"]) for r in db.execute(
                        "SELECT result_json FROM receipts WHERE run_id=? ORDER BY step", (run_id,))]
                # Tools are read/propose only. No network write can occur outside approval.
                call = plan.steps[index]
                result = self.tools.execute(call, tenant, receipts)
                with self.store.transaction() as db:
                    self.store.fenced(db, run_id, tenant, token)
                    db.execute("INSERT INTO receipts VALUES(?,?,?,?)",
                               (run_id, index, call.tool, canonical(result)))
                    new_status = "waiting_approval" if index == 2 else "running"
                    self.store.release(db, run_id, cursor=index + 1, status=new_status,
                                       attempts=0, next_attempt_at=0, last_error=None)
                    self.store.event(db, run_id, call.tool, "tool_completed", {"step": index, "tool": call.tool})
                    if new_status == "waiting_approval":
                        self.store.event(db, run_id, "engine", "approval_requested")
            else:  # approved: mock delivery + outbox ack share a transaction.
                with self.store.transaction() as db:
                    self.store.fenced(db, run_id, tenant, token)
                    decision = db.execute("SELECT approve FROM decisions WHERE run_id=?", (run_id,)).fetchone()
                    message = db.execute("SELECT * FROM outbox WHERE run_id=? AND status='pending'", (run_id,)).fetchone()
                    if not decision or not decision["approve"] or not message:
                        raise PermanentFailure("approval_or_outbox_missing")
                    case_id = "CASE-" + run_id
                    db.execute("INSERT INTO crm_cases VALUES(?,?,?,?,?)",
                               (case_id, run_id, tenant, message["payload_json"], self.store.clock()))
                    db.execute("UPDATE outbox SET status='delivered',delivered_at=? WHERE run_id=?",
                               (self.store.clock(), run_id))
                    self.store.release(db, run_id, status="completed", attempts=0, next_attempt_at=0, last_error=None)
                    self.store.event(db, run_id, "mock_crm", "case_created", {"case_id": case_id})
        except Conflict:
            # Another worker now owns the lease. The old worker must not change state.
            raise
        except Exception as exc:
            self._failure(run_id, tenant, token, exc)
        return self.store.get(run_id, tenant)

    def _failure(self, run_id, tenant, token, error):
        retryable = isinstance(error, TransientFailure)
        with self.store.transaction() as db:
            row = self.store.fenced(db, run_id, tenant, token)
            attempt = row["attempts"] + 1
            retry = retryable and attempt < self.max_attempts
            # Fixed codes: exception strings can contain secrets or document content.
            code = "dependency_temporarily_unavailable" if retryable else "step_validation_or_dependency_failure"
            self.store.release(db, run_id, attempts=attempt,
                               status=row["status"] if retry else "failed",
                               next_attempt_at=self.store.clock() + self.retry_base_seconds * 2 ** (attempt - 1) if retry else 0,
                               last_error=code)
            self.store.event(db, run_id, "engine", "retry_scheduled" if retry else "run_failed",
                             {"error_code": code, "attempt": attempt})

    def drain(self, run_id, tenant, max_ticks=8):
        """Advance ready steps only. Does not sleep or bypass persisted backoff."""
        for _ in range(max_ticks):
            state = self.tick(run_id, tenant)
            if (state["status"] not in ("queued", "running", "approved")
                    or state["next_attempt_at"] > self.store.clock()):
                return state
        return self.store.get(run_id, tenant)
