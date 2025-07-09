import time, requests, json, pytest

BACKEND = "http://localhost:5050"

@pytest.fixture(scope="session")
def users():
    u1 = f"user{int(time.time())}a"
    u2 = f"user{int(time.time())}b"
    for u in (u1, u2):
        requests.post(f"{BACKEND}/api/register", json={"username": u, "password": "pass"})
    def _token(user):
        r = requests.post(f"{BACKEND}/api/login", json={"username": user, "password": "pass"})
        return {"Authorization": f"Bearer {r.json()['auth_token']}"}
    return _token(u1), _token(u2)


def _set_baseline(device_id: int, cfg_text: str, proposer_h, approver_h):
    r = requests.post(f"{BACKEND}/api/devices/{device_id}/baseline/proposals", headers=proposer_h, json={"snapshot": cfg_text})
    pid = r.json()['id']
    requests.put(f"{BACKEND}/api/baseline/proposals/{pid}", headers=approver_h, json={"action":"approve"})


def test_critical_deviation(users):
    proposer, approver = users
    device_id = 1
    baseline = "interface Loopback0\n description baseline\n!"
    _set_baseline(device_id, baseline, proposer, approver)

    # new config with ACL change (critical)
    new_cfg = "interface Loopback0\n description baseline\n ip access-group 101 in\n!"
    r = requests.post(f"{BACKEND}/api/backups/save", headers=proposer, json={
        "device":"R15","command":"show run","method":"mock","content": new_cfg
    })
    assert r.status_code == 201

    # fetch deviations
    r = requests.get(f"{BACKEND}/api/devices/{device_id}/deviations", headers=proposer)
    assert r.status_code == 200
    data = r.json()
    assert len(data) >=1
    assert data[0]['severity'] == 'critical'
