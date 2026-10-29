"""Read-only portfolio tools. URLs, identity and customer bindings are server-owned.

The model cannot select destinations, credentials, tenants or invoice identifiers.
No approval/export endpoint or credential is available to these tools.
"""
import ipaddress
import json
import os
from urllib.parse import urlsplit, quote

import httpx

from .engine import LocalTools
from .planners import PermanentFailure, TransientFailure


def origin(value):
    parsed = urlsplit(value)
    loopback = parsed.hostname == "localhost"
    try:
        loopback = loopback or ipaddress.ip_address(parsed.hostname or "").is_loopback
    except ValueError:
        pass
    if (not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.path not in ("", "/")
            or not (parsed.scheme == "https" or (parsed.scheme == "http" and loopback))):
        raise ValueError("Tools require configured HTTPS origins or loopback HTTP")
    return value.rstrip("/")


class PortfolioTools(LocalTools):
    def __init__(self, accounting_url, rag_url, bindings, client=None):
        self.accounting_url, self.rag_url = origin(accounting_url), origin(rag_url)
        self.bindings, self.client = bindings, client

    def request(self, url, token, body=None):
        try:
            def send(client):
                with client.stream("POST" if body is not None else "GET", url,
                                   headers={"X-API-Key": token}, json=body) as response:
                    if response.status_code in (408, 429) or response.status_code >= 500:
                        raise TransientFailure("portfolio_dependency_unavailable")
                    if response.status_code != 200:
                        raise PermanentFailure("portfolio_dependency_rejected")
                    raw = bytearray()
                    for part in response.iter_bytes():
                        raw.extend(part)
                        if len(raw) > 256_000:
                            raise PermanentFailure("portfolio_response_too_large")
                    return json.loads(raw)
            if self.client:
                return send(self.client)
            with httpx.Client(timeout=10, follow_redirects=False, trust_env=False) as client:
                return send(client)
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            raise TransientFailure("portfolio_transport_failure") from exc
        except (ValueError, KeyError, TypeError) as exc:
            raise PermanentFailure("portfolio_invalid_response") from exc

    def execute(self, call, tenant, previous):
        if call.tool == "lookup_customer":
            customer = super().execute(call, tenant, previous)
            binding = self.bindings.get(tenant, {}).get(call.arguments.customer_id)
            if not binding:
                raise PermanentFailure("customer_binding_required")
            invoice = self.request(self.accounting_url + "/invoices/" + quote(binding["invoice_id"], safe=""),
                                   binding["accounting_key"])
            if invoice.get("tenant") != tenant or invoice.get("id") != binding["invoice_id"]:
                raise PermanentFailure("invoice_scope_mismatch")
            if invoice.get("status") not in {"pending_review", "blocked", "approved", "exported", "rejected"}:
                raise PermanentFailure("invoice_status_invalid")
            return {**customer, "invoice_id": invoice["id"], "invoice_status": invoice["status"],
                    "source": "accounting_api"}
        if call.tool == "check_policy":
            if len(previous) != 1:
                raise PermanentFailure("customer_evidence_required")
            binding = self.bindings.get(tenant, {}).get(previous[0].get("customer_id"))
            if not binding:
                raise PermanentFailure("customer_binding_required")
            answer = self.request(self.rag_url + "/ask", binding["rag_key"],
                                  {"question": "factuur goedkeuring", "top": 4})
            citations = answer.get("citations", [])
            # Source text is evidence, never executable policy. Fixed server rules still apply.
            if answer.get("abstained") is not False or not any(
                    c.get("document_id") == "invoice-policy" for c in citations):
                raise PermanentFailure("authorized_policy_source_required")
            return {"policy_id": "accounting-intake-v1", "human_approval_required": True,
                    "allowed_action": "create_mock_crm_case", "source": "rag_api",
                    "retrieval_mode": answer["mode"],
                    "citation_ids": [c["id"] for c in citations if c.get("document_id") == "invoice-policy"]}
        return super().execute(call, tenant, previous)


def configured_tools():
    mode = os.getenv("WORKFLOW_TOOLS_MODE", "local")
    if mode == "local":
        return LocalTools()
    if mode == "portfolio":
        return PortfolioTools(os.environ["ACCOUNTING_API_ORIGIN"], os.environ["RAG_API_ORIGIN"],
                              json.loads(os.environ["WORKFLOW_CUSTOMER_BINDINGS"]))
    raise ValueError("Unknown tools mode; no local fallback")
