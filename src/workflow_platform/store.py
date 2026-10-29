"""Short SQLite transactions; a lease token fences stale workers."""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sqlite3
import time
import uuid
from .models import Principal, RunRequest


class Conflict(Exception):
    pass


class Missing(Exception):
    pass


class Forbidden(Exception):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


class Store:
    def __init__(self, path="workflow.db", clock=time.time):
        self.path = str(path)
        self.clock = clock
        if self.path == ":memory:":
            raise ValueError("Use a file database: each operation opens its own connection")
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.transaction() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY, tenant TEXT NOT NULL, created_by TEXT NOT NULL,
                idempotency_key TEXT NOT NULL, request_hash TEXT NOT NULL, request_json TEXT NOT NULL,
                mode TEXT NOT NULL, status TEXT NOT NULL, plan_json TEXT, cursor INTEGER NOT NULL DEFAULT 0,
                attempts INTEGER NOT NULL DEFAULT 0, next_attempt_at REAL NOT NULL DEFAULT 0,
                lease_token TEXT, lease_until REAL NOT NULL DEFAULT 0, last_error TEXT,
                created_at REAL NOT NULL, updated_at REAL NOT NULL,
                UNIQUE(tenant, created_by, idempotency_key));
            CREATE TABLE IF NOT EXISTS events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL,
                at REAL NOT NULL, actor TEXT NOT NULL, kind TEXT NOT NULL, detail_json TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS receipts (
                run_id TEXT NOT NULL, step INTEGER NOT NULL, tool TEXT NOT NULL, result_json TEXT NOT NULL,
                PRIMARY KEY(run_id, step));
            CREATE TABLE IF NOT EXISTS decisions (
                run_id TEXT PRIMARY KEY, actor TEXT NOT NULL, approve INTEGER NOT NULL,
                reason TEXT NOT NULL, at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS outbox (
                id TEXT PRIMARY KEY, run_id TEXT UNIQUE NOT NULL, payload_json TEXT NOT NULL,
                status TEXT NOT NULL, created_at REAL NOT NULL, delivered_at REAL);
            CREATE TABLE IF NOT EXISTS crm_cases (
                id TEXT PRIMARY KEY, run_id TEXT UNIQUE NOT NULL, tenant TEXT NOT NULL,
                payload_json TEXT NOT NULL, created_at REAL NOT NULL);
            CREATE INDEX IF NOT EXISTS runs_tenant_status ON runs(tenant, status);
            CREATE INDEX IF NOT EXISTS events_run ON events(run_id, sequence);
            ''')

    @contextmanager
    def transaction(self):
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("BEGIN IMMEDIATE")
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def event(self, db, run_id, actor, kind, detail=None):
        db.execute("INSERT INTO events(run_id,at,actor,kind,detail_json) VALUES(?,?,?,?,?)",
                   (run_id, self.clock(), actor, kind, canonical(detail or {})))

    def row(self, db, run_id, tenant):
        row = db.execute("SELECT * FROM runs WHERE id=? AND tenant=?", (run_id, tenant)).fetchone()
        if row is None:
            raise Missing("run_not_found")
        return dict(row)

    def create(self, request: RunRequest, principal: Principal, key: str, mode: str):
        raw = canonical(request.model_dump())
        digest = hashlib.sha256(raw.encode()).hexdigest()
        with self.transaction() as db:
            previous = db.execute("SELECT * FROM runs WHERE tenant=? AND created_by=? AND idempotency_key=?",
                                  (principal.tenant, principal.subject, key)).fetchone()
            if previous:
                if previous["request_hash"] != digest:
                    raise Conflict("idempotency_key_reused_with_different_request")
                return previous["id"], False
            run_id, now = str(uuid.uuid4()), self.clock()
            db.execute('''INSERT INTO runs(id,tenant,created_by,idempotency_key,request_hash,request_json,
                       mode,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,'queued',?,?)''',
                       (run_id, principal.tenant, principal.subject, key, digest, raw, mode, now, now))
            self.event(db, run_id, principal.subject, "run_created", {"planner_mode": mode})
            return run_id, True

    def get(self, run_id, tenant):
        with self.transaction() as db:
            row = self.row(db, run_id, tenant)
            # Lease token and request hash are operational internals, not part of the API contract.
            result = {k: row[k] for k in ("id", "tenant", "created_by", "mode", "status", "cursor", "attempts",
                       "next_attempt_at", "last_error", "created_at", "updated_at")}
            result["request"] = json.loads(row["request_json"])
            result["plan"] = json.loads(row["plan_json"]) if row["plan_json"] else None
            result["tool_results"] = [dict(r) for r in db.execute(
                "SELECT step,tool,result_json FROM receipts WHERE run_id=? ORDER BY step", (run_id,))]
            for r in result["tool_results"]:
                r["result"] = json.loads(r.pop("result_json"))
            decision = db.execute("SELECT actor,approve,reason,at FROM decisions WHERE run_id=?", (run_id,)).fetchone()
            result["decision"] = dict(decision) if decision else None
            case = db.execute("SELECT id FROM crm_cases WHERE run_id=?", (run_id,)).fetchone()
            result["crm_case_id"] = case["id"] if case else None
            return result

    def list(self, tenant):
        with self.transaction() as db:
            return [dict(r) for r in db.execute(
                "SELECT id,status,mode,created_at,updated_at FROM runs WHERE tenant=? ORDER BY created_at DESC LIMIT 100",
                (tenant,))]

    def claim(self, run_id, tenant, lease_seconds=180):
        with self.transaction() as db:
            row = self.row(db, run_id, tenant)
            now = self.clock()
            if row["status"] not in ("queued", "running", "approved"):
                return None
            if row["next_attempt_at"] > now:
                return None
            if row["lease_token"] and row["lease_until"] > now:
                raise Conflict("worker_already_holds_lease")
            token = str(uuid.uuid4())
            db.execute("UPDATE runs SET lease_token=?,lease_until=? WHERE id=?", (token, now + lease_seconds, run_id))
            row["lease_token"], row["lease_until"] = token, now + lease_seconds
            return row

    def fenced(self, db, run_id, tenant, token):
        row = self.row(db, run_id, tenant)
        if row["lease_token"] != token or row["lease_until"] <= self.clock():
            raise Conflict("stale_worker_lease")
        return row

    def release(self, db, run_id, **updates):
        allowed = {"status", "plan_json", "cursor", "attempts", "next_attempt_at", "last_error"}
        if set(updates) - allowed:
            raise ValueError("Unsupported checkpoint update")
        fields = {**updates, "lease_token": None, "lease_until": 0, "updated_at": self.clock()}
        db.execute("UPDATE runs SET " + ",".join(f"{k}=?" for k in fields) + " WHERE id=?",
                   (*fields.values(), run_id))

    def decide(self, run_id, principal, approve, reason):
        with self.transaction() as db:
            row = self.row(db, run_id, principal.tenant)
            if "approver" not in principal.roles or principal.subject == row["created_by"]:
                raise Forbidden("independent_approver_required")
            if row["status"] != "waiting_approval":
                raise Conflict("run_is_not_waiting_for_approval")
            db.execute("INSERT INTO decisions VALUES(?,?,?,?,?)",
                       (run_id, principal.subject, int(approve), reason, self.clock()))
            if approve:
                receipt = db.execute("SELECT result_json FROM receipts WHERE run_id=? AND tool='prepare_case'",
                                     (run_id,)).fetchone()
                if not receipt:
                    raise Conflict("proposal_missing")
                payload = json.loads(receipt["result_json"])["proposal"]
                db.execute("INSERT INTO outbox VALUES(?,?,?,'pending',?,NULL)",
                           (str(uuid.uuid4()), run_id, canonical(payload), self.clock()))
            self.release(db, run_id, status="approved" if approve else "rejected")
            self.event(db, run_id, principal.subject, "approved" if approve else "rejected")
        return self.get(run_id, principal.tenant)

    def events(self, run_id, tenant):
        with self.transaction() as db:
            self.row(db, run_id, tenant)
            return [{**dict(r), "detail": json.loads(r["detail_json"])} for r in db.execute(
                "SELECT sequence,at,actor,kind,detail_json FROM events WHERE run_id=? ORDER BY sequence", (run_id,))]

    def cancel(self, run_id, principal, reason):
        """Cancellation and lease invalidation share the delivery transaction boundary."""
        with self.transaction() as db:
            row = self.row(db, run_id, principal.tenant)
            if "operator" not in principal.roles:
                raise Forbidden("operator_required")
            if row["status"] in ("completed", "rejected", "failed"):
                raise Conflict("terminal_run_cannot_be_cancelled")
            if row["status"] != "cancelled":
                db.execute("UPDATE outbox SET status='cancelled' WHERE run_id=? AND status='pending'", (run_id,))
                self.release(db, run_id, status="cancelled", next_attempt_at=0)
                self.event(db, run_id, principal.subject, "run_cancelled", {"reason": reason})
        return self.get(run_id, principal.tenant)

    def metrics(self, tenant):
        with self.transaction() as db:
            counts = {r["status"]: r["n"] for r in db.execute(
                "SELECT status,COUNT(*) AS n FROM runs WHERE tenant=? GROUP BY status", (tenant,))}
            retries = db.execute('''SELECT COUNT(*) FROM events e JOIN runs r ON r.id=e.run_id
                                    WHERE r.tenant=? AND e.kind='retry_scheduled' ''', (tenant,)).fetchone()[0]
            completed = db.execute('''SELECT AVG(updated_at-created_at) FROM runs
                                     WHERE tenant=? AND status='completed' ''', (tenant,)).fetchone()[0]
            return {"runs_by_status": counts, "retry_events": retries,
                    "mean_completed_seconds": completed,
                    "measurement_note": "Wall time includes human waiting; synthetic local runs only"}
