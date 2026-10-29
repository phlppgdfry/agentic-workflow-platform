# Read-only portfolio tools

The default `WORKFLOW_TOOLS_MODE=local` preserves the standalone fixture demo. With `portfolio`, the engine reads invoice state and authorized policy sources through HTTP. It still proposes only a local mock CRM case. It never approves or exports an invoice.

Server configuration (placeholder values, not credentials):

```text
WORKFLOW_TOOLS_MODE=portfolio
ACCOUNTING_API_ORIGIN=http://127.0.0.1:8000
RAG_API_ORIGIN=http://127.0.0.1:8084
WORKFLOW_CUSTOMER_BINDINGS={"demo":{"C-001":{"invoice_id":"SERVER_SELECTED_INVOICE_ID","accounting_key":"ACCOUNTING_AUDITOR_KEY","rag_key":"RAG_FINANCE_KEY"}}}
```

Each tenant/customer binding supplies its own credential pair. Model arguments cannot choose a URL, credential, invoice or tenant. Both endpoints must be HTTPS origins or loopback HTTP. Redirects are rejected, reads time out, responses are size-limited, wrong-tenant invoice responses fail closed, and missing/forbidden resources never silently fall back to fixtures. Keep downstream identities read-only. Rotating server bindings during an active run requires restarting that run; checkpointed receipts are historical evidence, not current permission grants.

The bounded plan retains `lookup_customer`, `check_policy`, `prepare_case`. The first enriches synthetic customer evidence with actual invoice status; the second requires an accessible `invoice-policy` source. Retrieved text does not modify the server's fixed approval rule. An injected source can still mislead a human; source availability is not proof of policy correctness.

`POST /runs/{id}/cancel` requires an operator and a reason. Cancellation invalidates the lease and pending outbox in one transaction. Completed/rejected/failed runs cannot be cancelled. This does not undo already delivered external effects. There is no hard thread termination for a running dependency call; its eventual checkpoint is fenced.

The optional orchestrated HTTP demonstration lives in [AI Transformation Playbook](https://github.com/phlppgdfry/ai-transformation-playbook), `integration/scenario.py`. Clone all six repositories as siblings, install each independently, then run from the playbook:

```bash
python3 -m integration.scenario --root ..
```

It creates temporary databases/random credentials, starts five loopback APIs, tests separate human approval boundaries, evaluates actual RAG/workflow responses and stops its own services. The scripted reviewers represent test identities, not observed human participation. Azure calls, tenant deployment and OCR are not part of this offline scenario.

Framework decision: current Context7 documentation was reviewed for [Microsoft Agent Framework](https://github.com/microsoft/agent-framework/blob/main/python/samples/03-workflows/checkpoint/checkpoint_with_human_in_the_loop.py) and [LangGraph](https://docs.langchain.com/oss/python/langgraph/interrupts). Both support durable human interaction. Keeping the explicit three-step engine preserves tested fencing and avoids migration without a branching requirement. MCP is deferred because no discovered-tool interoperability requirement exists.
