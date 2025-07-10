import requests, os

BACKEND_URL = os.getenv('BACKEND_URL', 'http://127.0.0.1:5050')

def test_network_status_endpoint(services_health):
    """Ensure /api/network/status returns expected schema."""
    url = f"{BACKEND_URL}/api/network/status"
    r = requests.get(url, timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert 'devices' in data and isinstance(data['devices'], list)
    if data['devices']:
        sample = data['devices'][0]
        assert {'hostname', 'status', 'cpu', 'mem'}.issubset(sample.keys())
