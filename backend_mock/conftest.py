import subprocess, time, requests, os, signal
import pytest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
APP_PATH = BASE_DIR / "app.py"

BACKEND_URL = "http://localhost:5050"


def _wait_until_ready(url: str, timeout: int = 10):
    """Poll a URL until it returns HTTP 200 or timeout."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=1)
            if r.status_code == 200:
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(0.5)
    return False


@pytest.fixture(scope="session", autouse=True)
def backend_server():
    """Start backend Flask server for the duration of the test session."""
    env = os.environ.copy()
    # Ensure Flask doesn't reload itself
    process = subprocess.Popen([
        "python3",
        str(APP_PATH)
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)

    if not _wait_until_ready(f"{BACKEND_URL}/api/health", timeout=15):
        # Output logs for debugging
        stdout, stderr = process.communicate(timeout=1)
        raise RuntimeError(
            "Backend server failed to start:\nSTDOUT:\n{}\nSTDERR:\n{}".format(stdout.decode(), stderr.decode())
        )

    yield

    # Teardown
    process.send_signal(signal.SIGTERM)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
