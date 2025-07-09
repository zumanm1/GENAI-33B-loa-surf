"""
Frontend test configuration and fixtures.
"""
import subprocess
import time
import requests
import os
import signal
import pytest
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR.parent / "backend_mock"
FRONTEND_APP_PATH = BASE_DIR / "app.py"
BACKEND_APP_PATH = BACKEND_DIR / "app.py"

# URLs
BACKEND_URL = "http://localhost:5050"
FRONTEND_URL = "http://localhost:5006"

def _wait_until_ready(url: str, timeout: int = 30):
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
    # Kill any existing backend servers
    subprocess.run(["pkill", "-f", str(BACKEND_APP_PATH)], stderr=subprocess.DEVNULL)
    
    # Start backend server
    process = subprocess.Popen(
        ["python3", str(BACKEND_APP_PATH)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for backend to be ready
    if not _wait_until_ready(f"{BACKEND_URL}/api/health", timeout=30):
        stdout, stderr = process.communicate(timeout=1)
        raise RuntimeError(
            f"Backend server failed to start:\nSTDOUT:\n{stdout.decode()}\nSTDERR:\n{stderr.decode()}"
        )
    
    print("Backend server is running.")
    yield
    
    # Teardown
    process.send_signal(signal.SIGTERM)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()

@pytest.fixture(scope="session", autouse=True)
def frontend_server():
    """Start frontend Flask server for the duration of the test session."""
    # Kill any existing frontend servers
    subprocess.run(["pkill", "-f", str(FRONTEND_APP_PATH)], stderr=subprocess.DEVNULL)
    
    # Start frontend server
    process = subprocess.Popen(
        ["python3", str(FRONTEND_APP_PATH)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for frontend to be ready
    if not _wait_until_ready(FRONTEND_URL, timeout=30):
        stdout, stderr = process.communicate(timeout=1)
        raise RuntimeError(
            f"Frontend server failed to start:\nSTDOUT:\n{stdout.decode()}\nSTDERR:\n{stderr.decode()}"
        )
    
    print("Frontend server is running.")
    yield
    
    # Teardown
    process.send_signal(signal.SIGTERM)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()

# Playwright fixtures are automatically provided by the pytest-playwright plugin
