import json
import tempfile
from pathlib import Path

import pytest
from flask import Flask

# Patch baseline_core.db to use a temporary DB per test
import importlib


@pytest.fixture()
def api_client(tmp_path, monkeypatch):
    # Redirect DB_PATH to temp
    db_mod = importlib.import_module("baseline_core.db")
    test_db = tmp_path / "baseline_test.db"
    monkeypatch.setattr(db_mod, "DB_PATH", test_db)

    # Re-init DB schema
    db_mod.init_db()

    # Create Flask app and register blueprint
    from baseline_core.routes import bp as baseline_bp  # noqa: E402

    app = Flask(__name__)
    app.register_blueprint(baseline_bp, url_prefix="/api")
    app.testing = True
    client = app.test_client()

    # Provide dummy auth header in every request
    client.environ_base["HTTP_AUTHORIZATION"] = "Bearer testtoken"
    return client


def test_duplicate_snapshot_returns_409(api_client):
    device_id = 1
    endpoint = f"/api/devices/{device_id}/baseline/proposals"
    payload = {"snapshot": "interface Gig0/0\n ip add 1.1.1.1 255.255.255.0", "comment": "first"}

    # First proposal should succeed
    resp1 = api_client.post(endpoint, data=json.dumps(payload), content_type="application/json")
    assert resp1.status_code == 201

    # Duplicate proposal with identical snapshot should be rejected
    resp2 = api_client.post(endpoint, data=json.dumps(payload), content_type="application/json")
    assert resp2.status_code == 409
    assert "identical snapshot" in resp2.get_json().get("error", "")
