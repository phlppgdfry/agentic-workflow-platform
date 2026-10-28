import hmac
import json
import os
from typing import Annotated
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from .engine import Engine
from .models import Decision, Principal, RunRequest
from .planners import configured_planner
from .store import Conflict, Forbidden, Missing, Store


def create_app(store=None, planner=None, principals=None):
    # No built-in API credentials. Missing server configuration fails at startup.
    mapping = principals if principals is not None else json.loads(os.environ["WORKFLOW_PRINCIPALS_JSON"])
    if not mapping or any(len(k) < 16 for k in mapping):
        raise ValueError("Configure nonempty API keys of at least 16 characters")
    credentials = {key: Principal.model_validate(value) for key, value in mapping.items()}
    db = store or Store(os.getenv("WORKFLOW_DB", "data/workflow.db"))
    engine = Engine(db, planner or configured_planner())
    app = FastAPI(title="Agentic Workflow Platform", version="0.1.0",
                  description="Approval-gated reference implementation. Fixture mode is deterministic; CRM is local mock storage.")
    app.state.store, app.state.engine = db, engine
    key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

    def authenticate(key: Annotated[str | None, Depends(key_header)]):
        if key:
            for candidate, principal in credentials.items():
                if hmac.compare_digest(key.encode(), candidate.encode()):
                    return principal
        raise HTTPException(401, "invalid_api_key")

    Auth = Annotated[Principal, Depends(authenticate)]

    def require(principal, *roles):
        if not set(principal.roles).intersection(roles):
            raise Forbidden("role_required")

    @app.exception_handler(Conflict)
    async def conflict_handler(request, exc):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(Missing)
    async def missing_handler(request, exc):
        return JSONResponse(status_code=404, content={"detail": "run_not_found"})

    @app.exception_handler(Forbidden)
    async def forbidden_handler(request, exc):
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.get("/health", tags=["operations"])
    def health():
        return {"status": "ok", "planner_mode": engine.planner.mode, "crm": "local_mock"}

    @app.post("/runs", status_code=201, tags=["workflows"])
    def create(request: RunRequest, principal: Auth,
               idempotency_key: Annotated[str, Header(min_length=8, max_length=100)]):
        require(principal, "builder")
        run_id, created = db.create(request, principal, idempotency_key, engine.planner.mode)
        return {"run": db.get(run_id, principal.tenant), "created": created}

    @app.get("/runs", tags=["workflows"])
    def list_runs(principal: Auth):
        return db.list(principal.tenant)

    @app.get("/runs/{run_id}", tags=["workflows"])
    def get_run(run_id: str, principal: Auth):
        return db.get(run_id, principal.tenant)

    @app.post("/runs/{run_id}/tick", tags=["workers"])
    def tick(run_id: str, principal: Auth):
        require(principal, "operator")
        return engine.tick(run_id, principal.tenant)

    @app.post("/runs/{run_id}/drain", tags=["workers"])
    def drain(run_id: str, principal: Auth):
        require(principal, "operator")
        return engine.drain(run_id, principal.tenant)

    @app.post("/runs/{run_id}/decision", tags=["approvals"])
    def decide(run_id: str, decision: Decision, principal: Auth):
        return db.decide(run_id, principal, decision.approve, decision.reason)

    @app.get("/runs/{run_id}/events", tags=["audit"])
    def events(run_id: str, principal: Auth):
        return db.events(run_id, principal.tenant)

    @app.get("/metrics", tags=["operations"])
    def metrics(principal: Auth):
        require(principal, "operator", "auditor")
        return db.metrics(principal.tenant)

    return app
