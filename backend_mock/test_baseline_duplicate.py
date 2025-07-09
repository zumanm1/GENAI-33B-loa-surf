import json
import os
import pytest
from backend_mock.app import app as backend_app, init_db


@pytest.fixture()
def client(tmp_path, monkeypatch):
    # point backend db to temp path
    db_path = tmp_path / "backend.db"
    backend_app.config['DATABASE'] = db_path
    init_db()

    backend_app.testing = True
    client = backend_app.test_client()
    client.environ_base["HTTP_AUTHORIZATION"] = "Bearer test"
    return client


def test_duplicate_snapshot_409(client):
    device_id = 1  # seeded by init_db()
    endpoint = f"/api/devices/{device_id}/baseline/proposals"
    payload = {"snapshot": "hostname R15", "comment": "dup"}

    # first should succeed
    resp1 = client.post(endpoint, data=json.dumps(payload), content_type="application/json")
    assert resp1.status_code == 201

    resp2 = client.post(endpoint, data=json.dumps(payload), content_type="application/json")
    assert resp2.status_code == 409
