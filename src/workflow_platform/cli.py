"""Self-contained synthetic demo. Generates no persistent credentials."""
import argparse
import json
from pathlib import Path
import tempfile
from .engine import Engine
from .models import Principal, RunRequest
from .planners import FixturePlanner
from .store import Store


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", help="Optional persistent database path; otherwise a temporary directory")
    args = parser.parse_args()
    temporary = tempfile.TemporaryDirectory() if not args.database else None
    try:
        path = args.database or str(Path(temporary.name) / "demo.db")
        store = Store(path)
        builder = Principal(subject="demo-requester", tenant="demo", roles=["builder", "operator"])
        approver = Principal(subject="demo-reviewer", tenant="demo", roles=["approver"])
        request = RunRequest(customer_id="C-001", message="Synthetic customer requests an accounting intake review.")
        run_id, _ = store.create(request, builder, "cli-demo-v1", "fixture")
        engine = Engine(store, FixturePlanner())
        state = engine.drain(run_id, "demo")
        print(json.dumps({"phase": "proposal", "run_id": run_id, "status": state["status"],
                          "mode": "fixture", "case_created": bool(state["crm_case_id"])}, indent=2))
        if state["status"] == "waiting_approval":
            store.decide(run_id, approver, True, "Demo-only independent approval of synthetic case")
        state = engine.drain(run_id, "demo")
        print(json.dumps({"phase": "after_approval", "status": state["status"],
                          "crm_case_id": state["crm_case_id"], "metrics": store.metrics("demo")}, indent=2))
        if state["status"] != "completed":
            raise SystemExit("Demo did not complete")
    finally:
        if temporary:
            temporary.cleanup()


if __name__ == "__main__":
    main()
