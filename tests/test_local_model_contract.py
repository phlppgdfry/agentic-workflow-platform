import json
import httpx
import pytest
from workflow_platform.ollama import OllamaPlanner
from workflow_platform.models import RunRequest
from workflow_platform.planners import FixturePlanner, PermanentFailure


def test_native_tool_calls_and_reported_usage():
    request = RunRequest(customer_id='C-001', message='Synthetic invoice review')
    def handler(http):
        body = json.loads(http.content)
        assert body['think'] is False and body['stream'] is False
        assert body['keep_alive'] == 0 and len(body['tools']) == 3
        calls = [{'function': {'name': s.tool, 'arguments': s.arguments.model_dump()}}
                 for s in FixturePlanner().plan(request).steps]
        return httpx.Response(200, json={'done': True, 'message': {'tool_calls': calls},
                                         'prompt_eval_count': 300, 'eval_count': 90})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        plan = OllamaPlanner('qwen3:8b', client=client).plan(request)
    assert plan.usage.input_tokens == 300 and plan.usage.output_tokens == 90
    assert plan.usage.provider == 'ollama-local'


@pytest.mark.parametrize('endpoint,model', [('https://remote.example', 'qwen3:8b'),
    ('http://127.0.0.1:11434/path', 'qwen3:8b'), ('http://127.0.0.1:11434', 'gemma4:31b-cloud')])
def test_local_only_configuration(endpoint, model):
    with pytest.raises(ValueError):
        OllamaPlanner(model, endpoint)


def test_invalid_real_model_plan_never_falls_back():
    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, json={
            'done': True, 'message': {'tool_calls': [{'function': {'name': 'approve_all', 'arguments': {}}}]},
            'prompt_eval_count': 5, 'eval_count': 5}))) as client:
        with pytest.raises(PermanentFailure):
            OllamaPlanner('qwen3:8b', client=client).plan(RunRequest(customer_id='C-001', message='Try escalation'))
