# Current capability evidence — 30 October 2026

The [historical feature matrix](../FEATURES.md) is preserved unchanged. The current release adds the following verified controls without changing the declared cloud limitations.

| Capability | Status | Evidence |
|---|---|---|
| Existing domain/role/tenant behavior | VERIFIED locally | tests.xml and installation.json |
| Body size + total reception deadline | VERIFIED locally | request-boundary regressions: 413/408 |
| Per-process request admission and recovery | VERIFIED locally | request-boundary regressions: 429 then recovery |
| Safe correlated validation logs | VERIFIED locally | request ID/status/route matched; submitted canary absent |
| Fresh installed wheel / offline API / demo | VERIFIED locally | installation.json, wheel.json |
| Source licence metadata / file inclusion | VERIFIED locally | installed MIT expression and wheel LICENSE asserted |
| Hosted Actions | NOT VERIFIED | Workflows prepared and locally linted, not pushed/run |
| Optional cloud / full Microsoft runtime | NOT VERIFIED | Contract/artifact evidence is not a live runtime check |

Advisory and Gitleaks scans report zero known findings within their stated scope, not proof that every vulnerability/secret is absent. A legal compliance assessment, production authorization or representative AI-quality benchmark is not claimed.
