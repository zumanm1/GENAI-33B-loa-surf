"""
End-to-end authentication flow tests for the Net-Swift Orchestrator.
Tests the complete user journey from registration through protected page access.

Note: Both backend and frontend servers must be running before executing these tests.
"""
import pytest
import time
import requests
from playwright.sync_api import expect, Page

# Test configuration
FRONTEND_URL = "http://localhost:5006"
BACKEND_URL = "http://localhost:5050"
TEST_USER = f"testuser_{int(time.time())}"  # Generate unique username
TEST_PASSWORD = "password123"

@pytest.fixture(scope="module")
def registered_user():
    """Create a test user directly via the backend API."""
    user_data = {
        "username": TEST_USER,
        "password": TEST_PASSWORD
    }
    response = requests.post(f"{BACKEND_URL}/api/register", json=user_data)
    assert response.status_code in [201, 409]  # 201 Created or 409 if already exists
    yield TEST_USER
    # No cleanup needed as test DB is ephemeral

def test_full_auth_flow(page: Page):
    """Test the complete authentication flow."""
    # Step 1: Register a new user with a unique name
    unique_user = f"flow_user_{int(time.time())}"
    
    page.goto(f"{FRONTEND_URL}/register")
    page.fill("input[name='username']", unique_user)
    page.fill("input[name='password']", TEST_PASSWORD)
    page.click("button[type='submit']")
    
    # Wait for redirect or response
    page.wait_for_load_state("networkidle")
    
    # Step 2: Login with the new user
    page.goto(f"{FRONTEND_URL}/login")
    page.fill("input[name='username']", unique_user)
    page.fill("input[name='password']", TEST_PASSWORD)
    page.click("button[type='submit']")
    
    # Wait for redirect to home page
    page.wait_for_load_state("networkidle")
    
    # Step 3: Verify we're logged in by checking the navbar
    navbar = page.locator("nav")
    expect(navbar).to_contain_text(unique_user)
    expect(navbar).to_contain_text("Logout")
    
    # Step 4: Access a protected page
    page.goto(f"{FRONTEND_URL}/devices")
    expect(page).to_have_url(f"{FRONTEND_URL}/devices")  # Should not redirect
    
    # Step 5: Logout
    page.click("text=Logout")
    page.wait_for_load_state("networkidle")
    
    # Step 6: Verify we're logged out by trying to access a protected page
    page.goto(f"{FRONTEND_URL}/devices")
    expect(page).to_have_url(f"{FRONTEND_URL}/login")  # Should redirect to login

def test_login_with_existing_user(page: Page, registered_user):
    """Test login with a pre-registered user."""
    page.goto(f"{FRONTEND_URL}/login")
    page.fill("input[name='username']", registered_user)
    page.fill("input[name='password']", TEST_PASSWORD)
    page.click("button[type='submit']")
    
    # Wait for redirect to home page
    page.wait_for_load_state("networkidle")
    
    # Verify we're logged in
    expect(page.locator("nav")).to_contain_text(registered_user)
    
    # Verify we can access protected pages
    page.goto(f"{FRONTEND_URL}/devices")
    expect(page).to_have_url(f"{FRONTEND_URL}/devices")

def test_invalid_login_attempt(page: Page):
    """Test login with invalid credentials."""
    page.goto(f"{FRONTEND_URL}/login")
    page.fill("input[name='username']", "nonexistent_user")
    page.fill("input[name='password']", "wrong_password")
    page.click("button[type='submit']")
    
    # Wait for response
    page.wait_for_load_state("networkidle")
    
    # Should still be on login page
    expect(page).to_have_url(f"{FRONTEND_URL}/login")
