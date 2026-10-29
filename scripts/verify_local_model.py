"""Opt-in genuine local inference; no model pull, downloads, cloud or external effects."""
import argparse
import json
from pathlib import Path
import tempfile
from workflow_platform.engine import Engine
from workflow_platform.models import Principal, RunRequest
from workflow_platform.ollama import OllamaPlanner
from workflow_platform.store import Store


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', required=True)
    parser.add_argument('--out', type=Path, default=Path('evidence/local-model-run.json'))
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as folder:
        store = Store(Path(folder) / 'local-model.db')
        builder = Principal(subject='synthetic-requester', tenant='demo', roles=['builder', 'operator'])
        reviewer = Principal(subject='synthetic-reviewer', tenant='demo', roles=['approver'])
        run, _ = store.create(RunRequest(customer_id='C-001', message='Prepare a review of a synthetic office invoice.'),
                              builder, 'genuine-local-model-v1', 'ollama')
        engine = Engine(store, OllamaPlanner(args.model))
        proposal = engine.drain(run, 'demo')
        report = {'execution': 'genuine local model tool calling; synthetic records and mock CRM',
                  'model': args.model, 'proposal_state': proposal, 'passed': False}
        if proposal['status'] == 'waiting_approval' and proposal['crm_case_id'] is None:
            store.decide(run, reviewer, True, 'Scripted independent reviewer checked the synthetic proposal')
            final = engine.drain(run, 'demo')
            report.update(final_state=final, events=store.events(run, 'demo'), passed=final['status'] == 'completed')
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({'passed': report['passed'], 'model': args.model,
                          'status': proposal['status'], 'evidence': str(args.out)}))
        return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
