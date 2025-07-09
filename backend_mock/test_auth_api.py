"""
Direct API tests for backend authentication endpoints.
These tests directly call the backend API without going through the frontend.
"""
import requests
import pytest
import random
import string

# Backend API URL
BACKEND_URL = "http://localhost:5050"

def random_username():
    """Generate a random username for testing."""
    return ''.join(random.choices(string.ascii_lowercase, k=8))

def test_register_api():
    """Test user registration API endpoint."""
    username = random_username()
    password = "testpass123"
    
    # Register a new user
    response = requests.post(
        f"{BACKEND_URL}/api/register",
        json={"username": username, "password": password}
    )
    
    # Check that registration was successful
    assert response.status_code == 201
    assert "User registered successfully" in response.json().get("message", "")
    
    # Try registering the same user again (should fail)
    response = requests.post(
        f"{BACKEND_URL}/api/register",
        json={"username": username, "password": password}
    )
    
    # Check that duplicate registration fails
    assert response.status_code == 409
    assert "already taken" in response.json().get("error", "")

def test_login_api():
    """Test user login API endpoint."""
    # Register a new user first
    username = random_username()
    password = "testpass123"
    
    requests.post(
        f"{BACKEND_URL}/api/register",
        json={"username": username, "password": password}
    )
    
    # Test successful login
    response = requests.post(
        f"{BACKEND_URL}/api/login",
        json={"username": username, "password": password}
    )
    
    # Check login success
    assert response.status_code == 200
    assert "Login successful" in response.json().get("message", "")
    assert "session" in response.cookies
    
    # Test login with wrong password
    response = requests.post(
        f"{BACKEND_URL}/api/login",
        json={"username": username, "password": "wrongpassword"}
    )
    
    # Check login failure
    assert response.status_code == 401
    assert "Invalid username or password" in response.json().get("error", "")

def test_protected_endpoint():
    """Test that protected endpoints require authentication."""
    # Try accessing a protected endpoint without authentication
    response = requests.get(f"{BACKEND_URL}/api/devices")
    
    # Should get unauthorized error
    assert response.status_code == 401
    
    # Register and login to get a session cookie
    username = random_username()
    password = "testpass123"
    
    requests.post(
        f"{BACKEND_URL}/api/register",
        json={"username": username, "password": password}
    )
    
    login_response = requests.post(
        f"{BACKEND_URL}/api/login",
        json={"username": username, "password": password}
    )
    
    # Get the session cookie
    session_cookie = login_response.cookies.get("session")
    
    # Try accessing the protected endpoint with the session cookie
    response = requests.get(
        f"{BACKEND_URL}/api/devices",
        cookies={"session": session_cookie}
    )
    
    # Should now be authorized
    assert response.status_code == 200
    assert isinstance(response.json(), list)

if __name__ == "__main__":
    print("Running backend authentication API tests...")
    # These tests assume the backend server is already running
