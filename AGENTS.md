# Working on this repository

Preserve the distinction between fixture mode, mocked Azure contract tests and live services. Never claim live cloud verification without evidence. The API must reject self-approval and cross-tenant access. New tools require schema, allowlist, customer-scope and retry/idempotency tests. Never add real customer records or secrets.

This project used the microsoft-foundry skill for Azure guidance. Before working on or answering questions about Foundry hosted agents, read the microsoft-foundry skill first. This application is currently a local FastAPI workflow, not a Foundry-hosted agent.

Run `python -m pytest -q`, `python -m workflow_platform.cli`, and `python scripts/export_openapi.py --check` after relevant changes.
