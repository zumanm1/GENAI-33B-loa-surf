"""
Debug tests for backend authentication.
"""
import requests
import random
import string
import json

# Backend API URL
BACKEND_URL = "http://localhost:5050"

def random_username():
    """Generate a random username for testing."""
    return ''.join(random.choices(string.ascii_lowercase, k=8))

def test_session_debug():
    """Debug test for session handling."""
    # Register a new user
    username = random_username()
    password = "testpass123"
    
    print(f"\n1. Registering new user: {username}")
    reg_response = requests.post(
        f"{BACKEND_URL}/api/register",
        json={"username": username, "password": password}
    )
    print(f"   Registration response: {reg_response.status_code}")
    print(f"   Response body: {reg_response.json()}")
    
    # Login with the new user
    print(f"\n2. Logging in as: {username}")
    login_response = requests.post(
        f"{BACKEND_URL}/api/login",
        json={"username": username, "password": password}
    )
    print(f"   Login response: {login_response.status_code}")
    print(f"   Response body: {login_response.json()}")
    print(f"   Cookies: {dict(login_response.cookies)}")
    
    # Get the session cookie
    session_cookie = login_response.cookies.get("session")
    print(f"   Session cookie: {session_cookie}")
    
    # Try accessing a protected endpoint
    print("\n3. Accessing protected endpoint with session cookie")
    devices_response = requests.get(
        f"{BACKEND_URL}/api/devices",
        cookies={"session": session_cookie}
    )
    print(f"   Devices response: {devices_response.status_code}")
    try:
        print(f"   Response body: {devices_response.json()}")
    except json.JSONDecodeError:
        print(f"   Response body (text): {devices_response.text}")
    
    # Try accessing the health endpoint (should be public)
    print("\n4. Accessing public health endpoint")
    health_response = requests.get(f"{BACKEND_URL}/api/health")
    print(f"   Health response: {health_response.status_code}")
    print(f"   Response body: {health_response.json()}")

if __name__ == "__main__":
    print("Running authentication debug tests...")
    test_session_debug()
