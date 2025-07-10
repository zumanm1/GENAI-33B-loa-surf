"""
Unit test for authentication flow between frontend and backend
"""
import pytest
import requests
import time
from unittest.mock import patch

# Test configuration
FRONTEND_URL = "http://localhost:5051"
BACKEND_URL = "http://localhost:5050"
TEST_USER = f"testuser_{int(time.time())}"
TEST_PASSWORD = "password123"

def test_register_and_login_flow():
    """Test the complete register and login flow"""
    # 1. Register a new user via backend directly
    register_response = requests.post(
        f"{BACKEND_URL}/api/register", 
        json={"username": TEST_USER, "password": TEST_PASSWORD}
    )
    assert register_response.status_code in [201, 409], f"Registration failed: {register_response.text}"
    
    # 2. Login via frontend
    session = requests.Session()
    login_response = session.post(
        f"{FRONTEND_URL}/login", 
        data={"username": TEST_USER, "password": TEST_PASSWORD}
    )
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    
    # 3. Try to access devices page
    devices_response = session.get(f"{FRONTEND_URL}/devices")
    assert devices_response.status_code == 200, f"Accessing devices page failed: {devices_response.text}"
    
    # 4. Try to access API devices endpoint
    api_devices_response = session.get(f"{FRONTEND_URL}/api/devices")
    assert api_devices_response.status_code == 200, f"API devices endpoint failed: {api_devices_response.text}"

def test_api_request_auth_cookies():
    """Test that API requests properly forward authentication cookies"""
    # This test will be run with mocked requests to isolate the cookie forwarding logic
    with patch('requests.request') as mock_request:
        # Setup mock response
        mock_response = mock_request.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        
        # Import the api_request function from the frontend app
        from frontend_py.app import api_request
        
        # Create a mock session with backend cookies
        with patch('frontend_py.app.session', {
            'username': 'testuser',
            'backend_session': 'test-session-value',
            'backend_user_id': '123'
        }):
            # Make an API request
            response = api_request('GET', '/api/devices')
            
            # Verify the cookies were forwarded correctly
            mock_request.assert_called_once()
            kwargs = mock_request.call_args[1]
            assert 'cookies' in kwargs
            assert kwargs['cookies'].get('session') == 'test-session-value'
            assert kwargs['cookies'].get('user_id') == '123'
