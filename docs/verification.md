# Verification evidence

Verified locally on 2026-10-28 using Python 3.13.18 on macOS. Exact installed dependency versions are in `requirements.lock`.

| Check | Actual result | Evidence |
|---|---|---|
| `python -m pytest -q` | 25 passed | [pytest output](../evidence/pytest.txt) |
| `python -m workflow_platform.cli` | Proposal paused, independent simulated approval, completed | [CLI output](../evidence/cli-demo.txt) |
| `python scripts/verify_demo.py` | HTTP create/replay, approval denial, review and one mock case | [JSON report](../evidence/demo-report.json) |
| `python scripts/export_openapi.py --check` | Passed against committed snapshot | [OpenAPI](openapi.json) |
| Editable package build/install | Passed with setuptools 84.2.1 | `pyproject.toml` and lockfile |
| Live Azure inference | Not run; no configured resource used | Adapter tested through `httpx.MockTransport` |
| Docker build / Compose startup | Not run in this verification | Recipe supplied, no container runtime claim |
| GitHub Actions hosted runs | Not observed during local verification | Workflow supplied; inspect actual GitHub run separately |
| Real CRM/ERP writes | Not implemented or attempted | Local SQLite mock tables only |

The 25 tests cover payload replay conflict; independent approval; rejection; restart after a read checkpoint and approval; lease contention and expiry fencing; persisted backoff and exhaustion; transient read recovery; tool/customer-scope abuse; unknown customer; mode mismatch; API input/role/tenant checks; Azure request shape, refusal, status classification and endpoint restrictions.

One upstream deprecation warning is present: Starlette 1.10.0 reports that its TestClient use with `httpx` is deprecated in favor of `httpx2`. Current contract tests still pass; the warning is retained in the evidence rather than suppressed. The live Azure adapter independently uses `httpx`.

The JSON report's latency is the wall time of a tiny local synthetic scenario with automated reviewer simulation. It is not human review time, a workload benchmark, an AI quality score or an estimate of production savings. Re-running the evidence script changes IDs and timing.
