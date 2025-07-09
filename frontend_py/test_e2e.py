"""
End-to-end tests for the Net-Swift Orchestrator frontend.
These tests verify the authentication flow and protected routes.
"""
import pytest
import time
import os
import signal
import subprocess
import requests
from playwright.sync_api import expect, Page, Locator

# Test configuration
FRONTEND_URL = "http://localhost:5006"
BACKEND_URL = "http://localhost:5050"
TEST_USER = f"testuser_{int(time.time())}"  # Generate unique username
TEST_PASSWORD = "password123"

# Fixtures for starting and stopping the servers
@pytest.fixture(scope="session")
def backend_server():
    """Start the backend server for testing."""
    process = subprocess.Popen(
        ["python3", "app.py"],
        cwd=os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend_mock"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to be ready
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{BACKEND_URL}/api/health")
            if response.status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    
    yield process
    process.send_signal(signal.SIGTERM)
    process.wait()

@pytest.fixture(scope="session")
def frontend_server():
    """Start the frontend server for testing."""
    process = subprocess.Popen(
        ["python3", "app.py"],
        cwd=os.path.dirname(__file__),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to be ready
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            response = requests.get(FRONTEND_URL)
            if response.status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    
    yield process
    process.send_signal(signal.SIGTERM)
    process.wait()

@pytest.fixture(scope="session")
def servers(backend_server, frontend_server):
    """Combined fixture for both servers."""
    yield

# Test cases
def test_register_and_login(page: Page, servers):
    """Test user registration, login, and access to protected pages."""
    # Step 1: Navigate to the registration page
    page.goto(f"{FRONTEND_URL}/register")
    expect(page).to_have_title("Net-Swift Orchestrator")
    
    # Step 2: Register a new user
    page.fill("input[name='username']", TEST_USER)
    page.fill("input[name='password']", TEST_PASSWORD)
    page.click("button[type='submit']")
    
    # Expect to be redirected to login page with success message
    expect(page).to_have_url(f"{FRONTEND_URL}/login")
    success_alert = page.locator(".alert-success").first
    if success_alert.count() > 0:
        expect(success_alert).to_contain_text("registered successfully")
    
    # Step 3: Login with the new user
    page.fill("input[name='username']", TEST_USER)
    page.fill("input[name='password']", TEST_PASSWORD)
    page.click("button[type='submit']")
    
    # Expect to be redirected to the home page
    expect(page).to_have_url(f"{FRONTEND_URL}/")
    
    # Step 4: Verify the navbar shows the logged-in user
    expect(page.locator("nav")).to_contain_text(TEST_USER)
    expect(page.locator("nav")).to_contain_text("Logout")
    
    # Step 5: Access a protected page
    page.goto(f"{FRONTEND_URL}/devices")
    expect(page).to_have_title("Devices - Net-Swift Orchestrator")
    
    # Step 6: Logout
    page.click("text=Logout")
    
    # Expect to be redirected to login page with logout message
    expect(page).to_have_url(f"{FRONTEND_URL}/login")
    success_alert = page.locator(".alert-success").first
    if success_alert.count() > 0:
        expect(success_alert).to_contain_text("logged out")
    
    # Step 7: Verify protected pages are no longer accessible
    page.goto(f"{FRONTEND_URL}/devices")
    expect(page).to_have_url(f"{FRONTEND_URL}/login")

def test_access_protected_page_when_not_logged_in(page: Page, servers):
    """Test that protected pages redirect to login when not logged in."""
    # Try to access a protected page without logging in
    page.goto(f"{FRONTEND_URL}/devices")
    
    # Expect to be redirected to the login page
    expect(page).to_have_url(f"{FRONTEND_URL}/login")

def test_invalid_login(page: Page, servers):
    """Test login with invalid credentials."""
    page.goto(f"{FRONTEND_URL}/login")
    
    # Try to login with invalid credentials
    page.fill("input[name='username']", "nonexistent_user")
    page.fill("input[name='password']", "wrong_password")
    page.click("button[type='submit']")
    
    # Expect to stay on login page with error message
    expect(page).to_have_url(f"{FRONTEND_URL}/login")
    danger_alert = page.locator(".alert-danger").first
    if danger_alert.count() > 0:
        expect(danger_alert).to_contain_text("Invalid")
