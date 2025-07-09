import os
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:5050")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5051")
AI_URL = os.getenv("AI_AGENT_URL", "http://127.0.0.1:5052")



def test_backend_devices():
    resp = requests.get(f"{BACKEND_URL}/api/devices", timeout=5)
    assert resp.status_code == 200
    data = resp.json()
    # Accept both legacy list format or new dict with devices key
    if isinstance(data, list):
        assert len(data) >= 1
    elif isinstance(data, dict) and "devices" in data:
        assert isinstance(data["devices"], list)
        assert len(data["devices"]) >= 1
    else:
        pytest.fail("/api/devices returned unexpected payload format")

def test_frontend_root_is_accessible():
    """Confirms the frontend root URL is available."""
    resp = requests.get(FRONTEND_URL, timeout=5)
    assert resp.status_code == 200
