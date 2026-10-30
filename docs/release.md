# Local release evaluation — 30 October 2026

This is a synthetic portfolio reference, ready for local technical inspection. It is not an Internet-facing production service. Hosted CI is **UNVERIFIED** until the branch is pushed with explicit authorization and its GitHub run actually succeeds. Existing dated evidence is preserved.

## Independent clean installation check

Use Python 3.13 for the reproduced environment. Package metadata supports Python 3.11+; additional hosted runtime validation is not claimed here. From a fresh checkout, this command needs only the standard library initially:

```bash
python3.13 scripts/release_check.py --output reports/release
```

It creates a temporary virtual environment, installs `requirements.lock`, builds a wheel using pinned setuptools, installs that wheel and checks the installed API/demo from an empty directory. It also runs the repository tests and OpenAPI drift check with those clean dependencies. The temporary environment is removed; `reports/release` retains the check record, JUnit, wheel/hash and declared dependency licences. Building the wheel does not prove a container or cloud deployment. Artifact hashes identify each build; byte-for-byte wheel determinism is not claimed.

For ordinary development, retain the README's `.venv` installation steps. Then:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python scripts/export_openapi.py --check
.venv/bin/python -m workflow_platform.cli
```

No model/cloud access is needed for these checks. Genuine local inference is optional in the workflow repository and separately labelled.

## Quality and security gates

```bash
python3.13 -m venv .quality-venv
.quality-venv/bin/python -m pip install -r requirements-quality.lock
.quality-venv/bin/python -m ruff check --select E4,E7,E9,F src tests scripts
.quality-venv/bin/python -m pip_audit -r requirements.lock --no-deps --disable-pip
```

Quality tools have their own environment so their dependencies do not alter the runtime lock. The same commands are prepared in CI. Pinned action commits, read-only GitHub permissions, no persisted checkout credentials and no PR-secret usage reduce release risk. Advisory scans can change as new findings are published; a future failure must be investigated rather than bypassed. Runtime versions are pinned, but distribution hashes are not yet required by pip.

The API admits at most 32 simultaneous application requests per process, bounds actual body bytes, and gives body reception a 30-second total deadline. Saturation returns 429; a stalled body returns 408. Metadata logs carry generated request IDs and omit submitted bodies/keys. These controls are not per-user rate limiting, distributed admission control, complete slow-connection protection or production authentication. Use a properly configured gateway and Entra identity before any real pilot.

## Artefacts, licences and limits

The source retains MIT licensing; wheels declare MIT and include LICENSE. Dependency licence metadata is inventoried in the new evidence; dependencies are not vendored. No model weights, customer dataset or third-party brand artwork is distributed. Review actual upstream terms for a chosen deployment/model; metadata is not a legal compliance assessment.

Current evidence is under `evidence/release-2026-10-30/`. Historical evidence remains in its original location. Source/debug database files and `.env` must never be staged. The local lock/advisory checks do not prove absence of all vulnerabilities or supply-chain compromise.

Use the [playbook repository](https://github.com/phlppgdfry/ai-transformation-playbook) as the optional six-repository demonstration entry point. This application remains independently runnable. Publication, PR creation, visibility changes, package releases and cloud/tenant operations require separate approval.

## Cleanup and troubleshooting

Stop only the process you started. The integration runner cleans up its own temporary services/databases; interrupt it normally. Development data under `data/` (or `var/` for governance) is separate from temporary test data. Keep audit evidence before deliberately resetting your own synthetic development database. Never run broad process kills or database deletion against another project.

An installation failure is captured in `reports/release/installation.json`; inspect the failing command and return code. A provider failure must remain visible—never switch to fixtures while claiming genuine execution. Missing keys produce authentication failures; unknown tenant resources remain inaccessible. Cloud modes and the full Microsoft runtime are still separately unverified.
