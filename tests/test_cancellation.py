import pytest
from test_workflows import new_run, ready, BUILDER, APPROVER
from workflow_platform.engine import Engine
from workflow_platform.planners import FixturePlanner
from workflow_platform.store import Store, Conflict, Forbidden


def test_cancellation_fences_inflight_worker(tmp_path):
    store = Store(tmp_path / 'cancel.db')
    identifier = new_run(store)
    claimed = store.claim(identifier, 'demo')
    assert store.cancel(identifier, BUILDER, 'Operator stopped task')['status'] == 'cancelled'
    with store.transaction() as db:
        with pytest.raises(Conflict):
            store.fenced(db, identifier, 'demo', claimed['lease_token'])
    assert Engine(store, FixturePlanner()).drain(identifier, 'demo')['status'] == 'cancelled'


def test_approved_pending_delivery_can_be_cancelled(tmp_path):
    store = Store(tmp_path / 'cancel.db')
    identifier = ready(store)
    store.decide(identifier, APPROVER, True, 'Independent review')
    with pytest.raises(Forbidden):
        store.cancel(identifier, APPROVER, 'Not an operator')
    for _ in range(2):
        assert store.cancel(identifier, BUILDER, 'Delivery no longer required')['status'] == 'cancelled'
    assert Engine(Store(store.path), FixturePlanner()).drain(identifier, 'demo')['crm_case_id'] is None
    with store.transaction() as db:
        assert db.execute('SELECT status FROM outbox').fetchone()[0] == 'cancelled'
    assert sum(e['kind'] == 'run_cancelled' for e in store.events(identifier, 'demo')) == 1
