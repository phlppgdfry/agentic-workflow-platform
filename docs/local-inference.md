# Genuine local tool calling

An opt-in native Ollama adapter uses an already installed local model. It makes a real model request to `/api/chat`; it is not the fixture planner. No SDK dependency was added. The normal demo/CI mode remains deterministic and makes no model calls.

```bash
.venv/bin/python scripts/verify_local_model.py --model qwen3:8b
```

This command was actually executed on 29 October 2026. The model returned native function calls, the application validated their schemas/order/customer scope, persisted tool receipts and waited for a separate reviewer identity before completing a local mock CRM case. [The actual report](../evidence/local-model-run.json) records the plan, model-reported token counts, measured latency, approval state and audit events. Scripted reviewer identities are test actors, not a real human UAT session. One successful synthetic request is not a broad model-quality benchmark.

For the API, configure `PLANNER_MODE=ollama` and `OLLAMA_MODEL=qwen3:8b`. `OLLAMA_ORIGIN` defaults to `http://127.0.0.1:11434` and must be loopback HTTP without paths/credentials. The selected model must already be installed; this adapter does not download models. Names containing `cloud` are rejected; administrators must also avoid aliases that proxy to cloud services. Never expose the local model daemon to an untrusted network.

The request disables thinking/streaming, limits generated tokens/context, sets a 90-second dependency timeout and unloads the model afterward. Redirects and oversized responses are rejected. Invalid/refused/incomplete/wrong-customer/tool plans fail closed; no fixture fallback is used. Ollama itself owns actual model execution resources; gateway concurrency and OS resource management remain deployment responsibilities.

The architecture is still one model planning call plus a deterministic three-step engine. The model does not receive tool results and replan adaptively. A future adaptive loop would need independent budgets, tool-output injection evaluation and justified business value. This implementation does not claim multi-agent collaboration.

The [playbook](https://github.com/phlppgdfry/ai-transformation-playbook) also supports a real-model integration run:

```bash
python3 -m integration.scenario --root .. --planner ollama --model qwen3:8b --output portfolio/integration-local-model-result.json
```

It uses actual accounting/RAG HTTP tools with the genuine local planner. Invoice fields remain explicit JSON, retrieval remains local extractive, and all effects remain local mocks. Azure OCR/inference is not verified by this local model run. Model usage and latency appear in the inspector only when actually recorded; no cloud cost is inferred from local tokens.

Official API documentation resolved/read with Context7 before implementation: [Ollama chat and tool calling](https://github.com/ollama/ollama/blob/main/docs/api.md). Contract tests inject responses; the separate report above records genuine inference.
