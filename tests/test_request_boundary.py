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
