# Operations runbook

## Inspect a stalled run

Read the run and chronological events using an authorized tenant key. `waiting_approval` is intentional: inspect all three tool results and ask the designated approver to decide. `next_attempt_at` in the future means persisted backoff; a tick before that time does nothing. `failed` is terminal; create a corrected new run with a new idempotency key after diagnosing the cause. The API does not offer a force-approve or erase-history endpoint.

`worker_already_holds_lease` (409) means another tick owns a live lease. Do not delete lease fields. If the process died, wait for the 180-second deadline and tick again. `stale_worker_lease` (409) means a slow worker lost ownership; only the new worker may checkpoint. The default live HTTP call has a 30-second timeout, below the lease duration. When modifying a tool, keep its bounded work below this deadline or add a safe heartbeat design.

`dependency_temporarily_unavailable` retries with bounded backoff. `step_validation_or_dependency_failure` fails closed without recording raw dependency text. For live diagnostics use the provider's own request trace tooling with appropriate access, avoiding secrets/documents in general logs. Current audit events intentionally trade diagnostic detail for disclosure resistance; no cloud trace exporter is configured.

## Restart and recovery

Keep the database and its volume. Restart the process with the same `WORKFLOW_DB`, principals and `PLANNER_MODE`. Queued/running/approved checkpoints can resume; waiting tasks remain waiting. Mode mismatch fails the run rather than changing its execution semantics. The automated restart test closes and reopens Store instances around tool and approval checkpoints.

The reference API uses worker-triggering routes, not an automatic poller. A local operator can call `/drain` to progress one run. For a real scheduler, authenticate as operator, poll ready runs in that tenant, obey the backoff timestamp and handle 409 leases. The current list endpoint is capped at 100 most recent runs and is not a complete scalable work queue.

## Backup and restore drill

Stop the API and all workers before copying the database and any WAL files, or use SQLite's online backup API. Do not copy only a live `.db` while WAL writes continue. Restore to an isolated directory and inspect row counts, pending approvals and outbox entries before resuming. A restore drill is not claimed as executed in this portfolio; document the actual drill in a production deployment.

## Incident procedure

Stop external action workers (this reference has only local mock writes), revoke affected keys, retain the database and event history, identify impacted run IDs and tenant, and involve the process owner. Do not approve a task merely to clear a backlog. Review the proposal and evidence. Rotate credentials and verify regression tests before restarting.

## Expected operating envelope

Single host, small synthetic datasets, short transactions. Metrics provide status counts, retry event count and mean completed wall time including human wait. There is no LLM token-cost accounting, distributed tracing backend, autoscaling or cloud SLA. Use the companion governance repository for broader evaluation; these workflow metrics alone do not measure semantic quality.
