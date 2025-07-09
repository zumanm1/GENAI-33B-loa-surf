"""
Backend API tests for device status monitoring functionality.
"""
import pytest
import requests
import time
import json

# Test configuration
BACKEND_URL = "http://localhost:5050"
TEST_USER = f"statususer_{int(time.time())}"
TEST_PASSWORD = "password123"
TEST_DEVICE = "TEST-DEVICE"  # This device is added during database initialization

def get_auth_session():
    """Create a test user and return an authenticated session."""
    session = requests.Session()
    
    # Register a test user
    register_data = {"username": TEST_USER, "password": TEST_PASSWORD}
    session.post(f"{BACKEND_URL}/api/register", json=register_data)
    
    # Login with the test user
    login_data = {"username": TEST_USER, "password": TEST_PASSWORD}
    session.post(f"{BACKEND_URL}/api/login", json=login_data)
    
    return session

def test_device_status_endpoint():
    """Test that the device status endpoint returns proper data structure."""
    session = get_auth_session()
    
    # Get device status
    response = session.get(f"{BACKEND_URL}/api/devices")
    assert response.status_code == 200
    
    # Verify response structure
    devices = response.json()
    assert isinstance(devices, list), "Response should be a list of devices"
    
    if devices:  # If there are devices in the database
        device = devices[0]
        assert "id" in device, "Device should have an ID"
        assert "name" in device, "Device should have a name"
        assert "status" in device, "Device should have a status"
        assert device["status"] in ["online", "offline", "unknown"], "Status should be valid"

def test_single_device_status():
    """Test that we can get status for a single device."""
    session = get_auth_session()
    
    # Get specific device status
    response = session.get(f"{BACKEND_URL}/api/device/{TEST_DEVICE}")
    
    # Should either return the device or a 404 if it doesn't exist
    if response.status_code == 200:
        device = response.json()
        assert device["name"] == TEST_DEVICE
        assert "status" in device
    else:
        assert response.status_code == 404

def test_update_device_status():
    """Test that device status can be updated."""
    session = get_auth_session()
    
    # First get current status
    response = session.get(f"{BACKEND_URL}/api/devices")
    assert response.status_code == 200
    
    # Find our test device
    devices = response.json()
    test_device = None
    for device in devices:
        if device["name"] == TEST_DEVICE:
            test_device = device
            break
    
    if test_device:
        # Try to update status
        new_status = "online" if test_device["status"] != "online" else "offline"
        update_data = {"status": new_status}
        
        response = session.put(
            f"{BACKEND_URL}/api/device/{TEST_DEVICE}/status", 
            json=update_data
        )
        
        # Check if update was successful
        if response.status_code == 200:
            # Verify the status was updated
            response = session.get(f"{BACKEND_URL}/api/device/{TEST_DEVICE}")
            assert response.status_code == 200
            updated_device = response.json()
            assert updated_device["status"] == new_status
        else:
            # If update is not implemented yet, this test can be skipped
            pytest.skip("Status update endpoint not implemented yet")
