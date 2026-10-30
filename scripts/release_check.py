"""Verify a built wheel in a fresh environment, outside the source tree.

Uses only Python's standard library before installing the repository's exact lock.
No model, tenant, cloud, Docker or publishing operation is performed.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import shutil
from pathlib import Path
import subprocess
import tempfile
import tomllib
import venv
import zipfile

SMOKE = r'''
import importlib, importlib.metadata, json, os, pathlib, secrets, sys, tempfile
from fastapi.testclient import TestClient
name = sys.argv[1]
profiles = {
 'enterprise-ai-accounting-copilot': ('accounting_copilot', '/invoices', True),
 'agentic-workflow-platform': ('workflow_platform', '/runs', True),
 'azure-ai-rag-knowledge-assistant': ('rag', '/ask', True),
 'enterprise-ai-evals-governance': ('evalgov', '/runs', True),
 'microsoft-copilot-studio-automation': ('automation', '/requests/missing', False)}
module, protected, console = profiles[name]
assert importlib.metadata.metadata(name)['License-Expression'] == 'MIT'
for key in list(os.environ):
 if key.startswith(('AZURE_', 'ACCOUNTING_', 'WORKFLOW_', 'RAG_', 'EVALGOV_', 'AUTOMATION_', 'OLLAMA_')) or key == 'PLANNER_MODE':
  del os.environ[key]
os.environ.update(PLANNER_MODE='fixture', WORKFLOW_TOOLS_MODE='local', RAG_PROVIDER='local', ACCOUNTING_AI_MODE='disabled')
os.environ['WORKFLOW_PRINCIPALS_JSON'] = json.dumps({secrets.token_urlsafe(32): {'subject':'package-check','tenant':'demo','roles':['auditor']}})
with tempfile.TemporaryDirectory() as tmp:
 os.chdir(tmp)
 package = importlib.import_module(module)
 assert pathlib.Path(package.__file__).resolve().is_relative_to(pathlib.Path(sys.prefix).resolve()), 'Source tree shadowed installed wheel'
 api = importlib.import_module(module + '.api')
 app = api.create_app() if module in ('workflow_platform', 'evalgov') else api.app
 with TestClient(app) as client:
  assert client.get('/health').status_code == 200
  response = client.post(protected, json={'question':'synthetic'}) if module == 'rag' else client.get(protected)
  assert response.status_code == 401
  if console:
   page = client.get('/console')
   assert page.status_code == 200 and '<html' in page.text and '<script' in page.text
 if module == 'rag':
  from rag.evaluate import benchmark
  assert all(r['permission_pass'] and r['expected_abstention_pass'] for r in benchmark()['results'])
 print(json.dumps({'installed_package':module, 'health':200, 'unauthenticated':401, 'console_packaged':console}))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('reports/release'))
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    project = tomllib.loads((repo / 'pyproject.toml').read_text())['project']['name']
    checks = []
    environment = {k: v for k, v in os.environ.items() if k not in ('PYTHONPATH', 'PYTHONHOME')}

    def run(command, cwd, expected=0):
        result = subprocess.run([str(c) for c in command], cwd=cwd, env=environment,
                                capture_output=True, text=True, timeout=240)
        checks.append({'command': [str(c) for c in command], 'cwd': str(cwd),
                       'exit_code': result.returncode, 'expected_exit': expected,
                       'passed': result.returncode == expected, 'stdout': result.stdout, 'stderr': result.stderr})
        if result.returncode != expected:
            raise RuntimeError('Release check failed: ' + ' '.join(str(c) for c in command[:4]))
        return result.stdout

    completed = False
    try:
        with tempfile.TemporaryDirectory(prefix='portfolio-install-') as folder:
            temporary = Path(folder)
            clean = temporary / 'env'
            venv.EnvBuilder(with_pip=True).create(clean)
            python = clean / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
            run([python, '-m', 'pip', 'install', '-r', repo / 'requirements.lock'], temporary)
            wheels = temporary / 'wheels'
            run([python, '-m', 'pip', 'wheel', '--no-deps', '--wheel-dir', wheels, repo], temporary)
            built = list(wheels.glob('*.whl'))
            if len(built) != 1:
                raise RuntimeError('Expected exactly one freshly built wheel')
            wheel = built[0]
            shutil.copy2(wheel, output / wheel.name)
            run([python, '-m', 'pip', 'install', '--no-deps', wheel], temporary)
            run([python, '-m', 'pip', 'check'], temporary)
            run([python, '-c', SMOKE, project], temporary)
            demos = {'enterprise-ai-accounting-copilot':'accounting_copilot.demo',
                     'agentic-workflow-platform':'workflow_platform.cli',
                     'azure-ai-rag-knowledge-assistant':'rag.demo',
                     'microsoft-copilot-studio-automation':'automation.demo'}
            if project in demos:
                run([python, '-m', demos[project]], temporary)
            else:
                run([python, '-m', 'evalgov.cli', '--fixture', 'good', '--out', temporary / 'good'], temporary)
                run([python, '-m', 'evalgov.cli', '--fixture', 'unsafe', '--out', temporary / 'unsafe'], temporary, expected=1)
            run([python, '-m', 'pytest', '-q', '--junitxml=' + str(output / 'tests.xml')], repo)
            run([python, 'scripts/export_openapi.py', '--check'], repo)
            licenses = run([python, '-c', "import importlib.metadata as m,json; print(json.dumps([{'name':d.metadata['Name'],'version':d.version,'license':d.metadata.get('License-Expression') or d.metadata.get('License','')[:200],'classifiers':[x for x in d.metadata.get_all('Classifier',[]) if x.startswith('License ::')]} for d in m.distributions()],indent=2))"], temporary)
            (output / 'dependency-licenses.json').write_text(licenses)
            with zipfile.ZipFile(wheel) as archive:
                manifest = {'wheel': wheel.name, 'sha256': hashlib.sha256(wheel.read_bytes()).hexdigest(),
                            'members': archive.namelist()}
                assert any(n.endswith('.dist-info/licenses/LICENSE') for n in archive.namelist()), 'License missing from wheel'
            (output / 'wheel.json').write_text(json.dumps(manifest, indent=2) + '\n')
            completed = True
    finally:
        report = {'executed_at': datetime.now(timezone.utc).isoformat(), 'repository': project,
                  'scope': 'new venv; locked dependencies; installed wheel; offline APIs/demos; source tests; no cloud',
                  'passed': completed and bool(checks) and all(c['passed'] for c in checks), 'checks': checks}
        (output / 'installation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'repository': project, 'passed': report['passed'], 'report': str(output / 'installation.json')}))


if __name__ == '__main__':
    main()
