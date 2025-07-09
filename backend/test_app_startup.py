import pytest
import requests
import time
from multiprocessing import Process

from app import app

# Define the expected host and port
HOST = "127.0.0.1"
PORT = 5050

def run_app():
    # Running in debug mode is not recommended for this kind of test,
    # as it can interfere with process management.
    app.run(host=HOST, port=PORT, debug=False)

@pytest.fixture(scope="module")
def server_process():
    """Fixture to run the Flask app in a separate process."""
    proc = Process(target=run_app, args=())
    proc.start()
    
    # Wait for the server to start
    time.sleep(3)
    
    yield
    
    # Teardown: terminate the server process
    proc.terminate()
    proc.join()

def test_server_is_alive(server_process):
    """
    GIVEN a running Flask application
    WHEN a GET request is made to the health check endpoint
    THEN the response should be successful (200 OK)
    """
    try:
        response = requests.get(f"http://{HOST}:{PORT}/api/health", timeout=5)
        assert response.status_code == 200
        assert response.json()['status'] == 'healthy'
    except requests.exceptions.ConnectionError as e:
        pytest.fail(f"Failed to connect to the server on port {PORT}. Is it running correctly? Error: {e}")
