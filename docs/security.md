# Security and responsible use

This portfolio uses synthetic fixtures only. Its controls are executable examples, not a GDPR or AI Act certification. Legal classification and organizational compliance require a concrete deployment, purposes, data flows and responsible human review.

| Threat | Implemented boundary | Remaining limitation |
|---|---|---|
| Request text instructs the agent to call shell or bypass approval | Tool allowlist, discriminated schema, fixed sequence, no shell/write tool, unconditional independent review | Prompt instruction filtering alone is not a security guarantee; humans can still approve a bad proposal |
| Model changes the customer or invents an action | Scope check, exact three-tool budget, unknown/inactive customer fails closed | Proposal wording can be misleading or factually incorrect and must be reviewed |
| Requester claims an approver role | Credentials map roles server-side; input models forbid extra fields | Static API keys require secure handling and rotation; no enterprise SSO |
| Cross-tenant reads | Every resource lookup filters tenant, returning 404 on mismatches | Principals can read all runs within their own tenant |
| Concurrent/recovered worker repeats a write | Lease fencing; read/propose steps only; atomic mock outbox and case; unique run ID | Exactly-once writes to a real network API are not implemented |
| Dependency logs disclose secrets | Audit persists fixed error codes, not exception strings or response bodies | Requests/proposals are persisted locally in plaintext; OS/database access is privileged |
| Attacker supplies a model endpoint | Endpoint is operator config only; HTTPS Azure resource host suffixes; redirects disabled | No DNS pinning; deploy within enterprise egress controls if needed |
| Audit modification | No API mutation of audit events | SQLite administrator can alter events; no WORM storage or cryptographic chain |

API keys should be generated independently for each identity. Keep `.env` out of Git; never put Azure keys in examples, test snapshots or query strings. The local process and database directory should be owned by the deployment account. Compose runs as an unprivileged user and only binds the host loopback interface; use an authenticated TLS gateway before any network exposure.

Azure mode sends the request text to the configured resource. Fixture mode does not. The health endpoint and run records state the mode explicitly. Switching modes is not permitted for an existing run. The adapter has no silent fallback.

## Before a real pilot

Choose an accountable process owner, document purposes and approved data classes, validate the model/data processing configuration and retention, arrange human override and incident ownership, and run a security review in the actual tenant. Replace static keys with validated Entra tokens; assign least-privilege workload permissions; add organizational monitoring and deployment-specific controls. Test recovery from backups and verify remote connector idempotency. None of those steps should be inferred from these local tests.
