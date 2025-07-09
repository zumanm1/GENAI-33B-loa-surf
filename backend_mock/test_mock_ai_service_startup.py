import subprocess
import time
import requests
import pytest

# Define the URL for the mock service
SERVICE_URL = "http://127.0.0.1:5052"

@pytest.fixture(scope="module")
def mock_ai_service():
    """Fixture to start and stop the mock AI service."""
    # Command to start the service
    command = ["python3", "mock_ai_service.py"]
    
    # Start the service as a background process
    process = subprocess.Popen(command, cwd="/Users/macbook/GENAI-33-LOVEAB/net-swift-orchestrator/backend_mock")
    
    # Give the server a moment to start up
    time.sleep(3)  # Increased wait time for stability
    
    # Yield the process object to the test
    yield process
    
    # Teardown: terminate the process after the test completes
    process.terminate()
    process.wait()

def test_service_health_check(mock_ai_service):
    """Tests if the mock AI service is running and responds to the health check."""
    try:
        response = requests.get(f"{SERVICE_URL}/health", timeout=5)
        # Assert that the request was successful
        assert response.status_code == 200
        # Assert that the response content is as expected
        assert response.json() == {"status": "ok"}
        print(f"\nHealth check successful: {response.status_code} {response.json()}")
    except requests.exceptions.ConnectionError as e:
        pytest.fail(f"Failed to connect to the mock AI service at {SERVICE_URL}. Error: {e}")
