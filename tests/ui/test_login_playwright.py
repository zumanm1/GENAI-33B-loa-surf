import re
from playwright.sync_api import Page, expect

# Define the base URL for the frontend application
BASE_URL = "http://127.0.0.1:5051"

import secrets

def test_registration_and_login(page: Page):
    """
    This test automates a full user journey:
    1. Navigates to the registration page.
    2. Creates a new, unique user.
    3. Verifies redirection to the login page.
    4. Logs in with the new credentials.
    5. Verifies successful redirection to the dashboard.
    6. Asserts that the dashboard displays correctly.
    """
    # Generate unique user credentials for this test run
    test_username = f"testuser_{secrets.token_hex(4)}"
    test_password = "a_secure_password"

    # 1. Navigate to the registration page
    page.goto(f"{BASE_URL}/register")
    expect(page).to_have_title(re.compile("Register"))

    # 2. Fill in the registration form and submit
    page.locator('input[name="username"]').fill(test_username)
    page.locator('input[name="password"]').fill(test_password)
    page.get_by_role("button", name="Register").click()

    # 3. Verify redirection to the login page
    expect(page).to_have_url(re.compile("login"))
    # Also check for the success message
    expect(page.locator(".alert-success")).to_be_visible()

    # 4. Log in with the new credentials
    page.locator('input[name="username"]').fill(test_username)
    page.locator('input[name="password"]').fill(test_password)
    page.get_by_role("button", name="Login").click()

    # 5. Verify redirection to the dashboard
    expect(page).to_have_url(BASE_URL + "/")

    # 6. Assert that a key element from the dashboard is visible
    dashboard_heading = page.locator("h5:has-text('System Status')")
    expect(dashboard_heading).to_be_visible()

    print(f"\nPlaywright test successful: Registered and logged in with user '{test_username}'.")
