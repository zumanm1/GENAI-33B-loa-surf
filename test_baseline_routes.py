import json, time, secrets
import pytest
import requests

BACKEND_URL = "http://localhost:5050"

@pytest.fixture(scope="session")
def auth_headers():
    # Register+login a pair of users (proposer & approver)
    u1 = f"proposer_{int(time.time())}"
    u2 = f"approver_{int(time.time())}"
    for u in (u1, u2):
        requests.post(f"{BACKEND_URL}/api/register", json={"username": u, "password": "pass"})
    # login
    def _login(user):
        r = requests.post(f"{BACKEND_URL}/api/login", json={"username": user, "password": "pass"})
        r.raise_for_status()
        token = r.json().get("auth_token")
        return {"Authorization": f"Bearer {token}"}
    return _login(u1), _login(u2)


def test_proposal_approve_flow(auth_headers):
    proposer_headers, approver_headers = auth_headers
    device_id = 1  # R15 seeded in main DB
    cfg_text = "interface Loopback123\n description test\n!"
    # create proposal
    r = requests.post(
        f"{BACKEND_URL}/api/devices/{device_id}/baseline/proposals",
        headers=proposer_headers,
        json={"snapshot": cfg_text, "comment": "test baseline"},
    )
    assert r.status_code == 201
    pid = r.json()["id"]
    # approve with different user
    r = requests.put(
        f"{BACKEND_URL}/api/baseline/proposals/{pid}",
        headers=approver_headers,
        json={"action": "approve"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "approved"
    # fetch baseline
    r = requests.get(f"{BACKEND_URL}/api/devices/{device_id}/baseline", headers=proposer_headers)
    assert r.status_code == 200
    data = r.json()
    assert "text" in data and cfg_text.splitlines()[0] in data["text"]
