"""Generate actual, local synthetic evidence from API requests (no cloud calls)."""
import json
from pathlib import Path
import platform
import tempfile
from fastapi.testclient import TestClient
from workflow_platform.api import create_app
from workflow_platform.planners import FixturePlanner
from workflow_platform.store import Store

with tempfile.TemporaryDirectory() as folder:
    store = Store(Path(folder) / "evidence.db")
    principals = {
        "evidence-builder-123": {"subject": "requester", "tenant": "demo", "roles": ["builder", "operator"]},
        "evidence-reviewer-123": {"subject": "reviewer", "tenant": "demo", "roles": ["approver", "auditor"]},
    }
    with TestClient(create_app(store, FixturePlanner(), principals)) as client:
        headers = {"X-API-Key": "evidence-builder-123", "Idempotency-Key": "evidence-request-001"}
        request = {"customer_id": "C-001", "message": "Synthetic accounting-intake evidence scenario."}
        created = client.post("/runs", headers=headers, json=request)
        assert created.status_code == 201
        run_id = created.json()["run"]["id"]
        replay = client.post("/runs", headers=headers, json=request)
        assert replay.json()["created"] is False
        ready = client.post(f"/runs/{run_id}/drain", headers=headers)
        assert ready.json()["status"] == "waiting_approval"
        assert ready.json()["crm_case_id"] is None
        denied = client.post(f"/runs/{run_id}/decision", headers=headers,
                             json={"approve": True, "reason": "Attempt self approval without permission"})
        assert denied.status_code == 403
        decision = client.post(f"/runs/{run_id}/decision", headers={"X-API-Key": "evidence-reviewer-123"},
                               json={"approve": True, "reason": "Reviewed synthetic customer and policy evidence"})
        assert decision.status_code == 200
        finished = client.post(f"/runs/{run_id}/drain", headers=headers)
        assert finished.json()["status"] == "completed"
        repeated = client.post(f"/runs/{run_id}/drain", headers=headers)
        assert repeated.json()["crm_case_id"] == finished.json()["crm_case_id"]
        events = client.get(f"/runs/{run_id}/events", headers=headers).json()
        with store.transaction() as db:
            case_count = db.execute("SELECT COUNT(*) FROM crm_cases").fetchone()[0]
        report = {
            "scenario": "local synthetic HTTP end-to-end", "python": platform.python_version(),
            "planner_mode": "fixture", "live_azure_called": False, "crm": "local_mock",
            "run_id": run_id, "created_status": created.status_code,
            "replay_created_new_run": replay.json()["created"],
            "before_approval_status": ready.json()["status"], "case_before_approval": ready.json()["crm_case_id"],
            "self_approval_http_status": denied.status_code, "reviewer_decision_status": decision.status_code,
            "final_status": finished.json()["status"], "case_count_after_repeated_delivery": case_count,
            "metrics": store.metrics("demo"),
            "event_sequence": [{"sequence": e["sequence"], "kind": e["kind"]} for e in events],
        }
        assert case_count == 1
        target = Path(__file__).resolve().parents[1] / "evidence" / "demo-report.json"
        target.parent.mkdir(exist_ok=True)
        target.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
