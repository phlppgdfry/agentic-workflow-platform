# Feature evidence matrix — 29 October 2026

Status vocabulary: **VERIFIED** means the stated local behavior was executed; **IMPLEMENTED BUT NOT VERIFIED** means code/artifacts exist without live acceptance; **MOCKED** means a deliberately substituted external effect; **DOCUMENTED ONLY** is a design/runbook; **PLANNED** is future work. Local tests do not prove production safety, real customer use or legal compliance.

Verification commands and results are in [verification-2026-10-29.json](verification-2026-10-29.json). Original 28 October evidence is retained as historical evidence. The pinned dependency audit reports no known advisories at scan time, not absence of all vulnerabilities. Request logs omit bodies, query strings and credentials.

| Feature | Status | Evidence / limitation |
|---|---|---|
| Durable steps, retries, leases/fencing, independent approval | VERIFIED | tests/test_workflows.py |
| Invoice/policy HTTP tools and scoped identities | VERIFIED | tests/test_portfolio_tools.py; playbook portfolio/integration-result.json |
| Cancellation of queued/approved/inflight work | VERIFIED | tests/test_cancellation.py |
| Workflow inspector and approval actions | VERIFIED | playbook portfolio/browser-qa.json; screenshots/desktop.png |
| Native local Qwen tool calling, token usage and planning latency | VERIFIED | local-model-run.json; genuine inference, synthetic request; not a representative model benchmark |
| Deterministic planner and local CRM | MOCKED | fixture planner contains no LLM; CRM writes local tables |
| Azure function tool calling | IMPLEMENTED BUT NOT VERIFIED | mock HTTP contracts pass; live execution/quality unavailable |
| Agent Framework/LangGraph/MCP adoption | DOCUMENTED ONLY | docs/portfolio-integration.md explains deferral |
| Entra/distributed workers/live model telemetry | PLANNED | existing runbook and architecture |
