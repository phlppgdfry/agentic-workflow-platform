"""Export deterministic OpenAPI without creating production credentials or persistent data."""
import argparse
import json
from pathlib import Path
import tempfile
from workflow_platform.api import create_app
from workflow_platform.planners import FixturePlanner
from workflow_platform.store import Store

parser = argparse.ArgumentParser()
parser.add_argument("--check", action="store_true")
args = parser.parse_args()
with tempfile.TemporaryDirectory() as folder:
    app = create_app(Store(Path(folder) / "schema.db"), FixturePlanner(), {
        "schema-export-key-1234": {"subject": "schema", "tenant": "demo", "roles": ["auditor"]}})
    text = json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n"
path = Path(__file__).resolve().parents[1] / "docs" / "openapi.json"
if args.check:
    if path.read_text() != text:
        raise SystemExit("OpenAPI drift: run python scripts/export_openapi.py")
else:
    path.write_text(text)
