import pytest
import requests
import time
import sys
import os
from multiprocessing import Process

# Add project paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from frontend_py.app import app as frontend_app
from backend.app import app as backend_app

# --- Configuration ---
FRONTEND_HOST = "127.0.0.1"
FRONTEND_PORT = 5051
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 5050

# --- Test Server Processes ---
def run_frontend():
    frontend_app.run(host=FRONTEND_HOST, port=FRONTEND_PORT, debug=False)

def run_backend():
    backend_app.run(host=BACKEND_HOST, port=BACKEND_PORT, debug=False)

@pytest.fixture(scope="module")
def services():
    """Fixture to run both backend and frontend servers in separate processes."""
    backend_proc = Process(target=run_backend, args=(), daemon=True)
    frontend_proc = Process(target=run_frontend, args=(), daemon=True)
    
    backend_proc.start()
    time.sleep(3) # Wait for backend to initialize
    
    frontend_proc.start()
    time.sleep(2) # Wait for frontend to initialize

    yield
    
    # Teardown
    frontend_proc.terminate()
    backend_proc.terminate()

# --- Functional Test ---

def test_frontend_connects_backend(services):
    """Ensure the frontend page loads without backend connection errors."""
    login_url = f"http://{FRONTEND_HOST}:{FRONTEND_PORT}/login"

    # Attempt request to frontend
    resp = requests.get(login_url, timeout=10)
    assert resp.status_code == 200, f"Expected 200 from frontend, got {resp.status_code}"

    # Ensure no backend connection error banner in HTML
    assert "Error connecting to backend" not in resp.text, "Frontend shows backend connection error"
