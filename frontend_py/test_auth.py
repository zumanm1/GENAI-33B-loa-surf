"""
Simple authentication tests for the Net-Swift Orchestrator frontend.
These tests verify the authentication flow and protected routes.

Note: Both backend and frontend servers must be running before executing these tests.
"""
import pytest
import time
from playwright.sync_api import expect, Page

# Test configuration
FRONTEND_URL = "http://localhost:5006"
TEST_USER = f"testuser_{int(time.time())}"  # Generate unique username
TEST_PASSWORD = "password123"

def test_login_redirect(page: Page):
    """Test that protected pages redirect to login when not logged in."""
    # Try to access a protected page without logging in
    page.goto(f"{FRONTEND_URL}/devices")
    
    # Expect to be redirected to the login page
    expect(page).to_have_url(f"{FRONTEND_URL}/login")

def test_login_page_loads(page: Page):
    """Test that the login page loads correctly."""
    page.goto(f"{FRONTEND_URL}/login")
    expect(page).to_have_title("Net-Swift Orchestrator")
    
    # Check that the login form exists
    expect(page.locator("form")).to_be_visible()
    expect(page.locator("input[name='username']")).to_be_visible()
    expect(page.locator("input[name='password']")).to_be_visible()
    expect(page.locator("button[type='submit']")).to_be_visible()

def test_register_page_loads(page: Page):
    """Test that the registration page loads correctly."""
    page.goto(f"{FRONTEND_URL}/register")
    expect(page).to_have_title("Net-Swift Orchestrator")
    
    # Check that the registration form exists
    expect(page.locator("form")).to_be_visible()
    expect(page.locator("input[name='username']")).to_be_visible()
    expect(page.locator("input[name='password']")).to_be_visible()
    expect(page.locator("button[type='submit']")).to_be_visible()
