from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel
from workflow_platform.security import install_security


class Input(BaseModel):
    number: int


def client():
    app = FastAPI()
    install_security(app, max_bytes=64)

    @app.post('/value')
    def value(body: Input):
        return {'value': body.number}
    return TestClient(app)


def test_actual_stream_limit_and_correlation():
    c = client()
    response = c.post('/value', content=iter([b'x' * 40, b'y' * 40]))
    assert response.status_code == 413
    assert len(response.headers['x-request-id']) == 36
    assert c.post('/value', json={'number': 2}).json() == {'value': 2}


def test_invalid_input_never_echoed():
    response = client().post('/value', json={'number': 'sensitive-canary'})
    assert response.status_code == 422
    assert 'sensitive-canary' not in response.text


def test_slow_body_has_total_deadline():
    import asyncio
    from workflow_platform.security import RequestBoundary

    async def exercise():
        sent = []
        async def never_called(scope, receive, send):
            raise AssertionError('Incomplete request must not reach application')
        async def receive():
            await asyncio.sleep(1)
        async def send(message):
            sent.append(message)
        await RequestBoundary(never_called, body_timeout=.01)(
            {'type': 'http', 'method': 'POST', 'path': '/value'}, receive, send)
        assert sent[0]['status'] == 408
    asyncio.run(exercise())


def test_admission_rejects_without_blocking_and_recovers():
    import asyncio
    from workflow_platform.security import RequestBoundary

    async def exercise():
        entered, release = asyncio.Event(), asyncio.Event()
        async def app(scope, receive, send):
            entered.set()
            await release.wait()
            await send({'type': 'http.response.start', 'status': 200, 'headers': []})
            await send({'type': 'http.response.body', 'body': b'ok'})
        async def receive():
            return {'type': 'http.request', 'body': b''}
        async def discard(message):
            pass
        boundary = RequestBoundary(app, max_active=1)
        scope = {'type': 'http', 'method': 'GET', 'path': '/health'}
        first = asyncio.create_task(boundary(scope, receive, discard))
        await entered.wait()
        messages = []
        async def collect(message):
            messages.append(message)
        await boundary(scope, receive, collect)
        assert messages[0]['status'] == 429
        release.set()
        await first
        messages.clear()
        await boundary(scope, receive, collect)
        assert messages[0]['status'] == 200
    asyncio.run(exercise())


def test_validation_log_is_correlated_without_submitted_values(caplog):
    import json
    import logging
    with caplog.at_level(logging.INFO, logger='uvicorn.error'):
        response = client().post('/value', json={'number': 'sensitive-log-canary'})
    events = [json.loads(record.getMessage()) for record in caplog.records if record.name == 'uvicorn.error']
    assert events[-1]['status'] == 422 and events[-1]['route'] == '/value'
    assert events[-1]['request_id'] == response.headers['x-request-id']
    assert 'sensitive-log-canary' not in caplog.text
