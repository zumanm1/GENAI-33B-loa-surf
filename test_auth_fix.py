"""
Test script to verify authentication fix between frontend and backend
"""
import requests
import time
import sys
import json

# Configuration
FRONTEND_URL = "http://localhost:5006"
BACKEND_URL = "http://localhost:5050"
TEST_USER = f"testuser_{int(time.time())}"
TEST_PASSWORD = "password123"

def print_step(message):
    """Print a step message with formatting"""
    print("\n" + "="*80)
    print(f"STEP: {message}")
    print("="*80)

def main():
    """Run the authentication test flow"""
    session = requests.Session()
    
    # Step 1: Register a new user
    print_step("Registering new test user")
    register_response = requests.post(
        f"{BACKEND_URL}/api/register", 
        json={"username": TEST_USER, "password": TEST_PASSWORD}
    )
    print(f"Register response: {register_response.status_code}")
    print(register_response.text)
    
    if register_response.status_code not in [201, 409]:
        print("❌ Registration failed")
        sys.exit(1)
    
    # Step 2: Login via frontend
    print_step("Logging in via frontend")
    login_response = session.post(
        f"{FRONTEND_URL}/login", 
        data={"username": TEST_USER, "password": TEST_PASSWORD},
        allow_redirects=False
    )
    print(f"Login response: {login_response.status_code}")
    
    if login_response.status_code not in [200, 302]:
        print("❌ Login failed")
        sys.exit(1)
    else:
        print("✅ Login successful")
    
    # Step 3: Access devices page
    print_step("Accessing devices page")
    devices_response = session.get(f"{FRONTEND_URL}/devices")
    print(f"Devices page response: {devices_response.status_code}")
    
    if devices_response.status_code == 200:
        print("✅ Devices page accessible")
    else:
        print("❌ Devices page access failed")
    
    # Step 4: Access retrieve page (previously failing with 401)
    print_step("Accessing retrieve page (previously failing)")
    retrieve_response = session.get(f"{FRONTEND_URL}/retrieve")
    print(f"Retrieve page response: {retrieve_response.status_code}")
    
    if retrieve_response.status_code == 200:
        print("✅ Retrieve page accessible")
    else:
        print("❌ Retrieve page access failed")
    
    # Step 5: Access backups page (previously failing with 401)
    print_step("Accessing backups page (previously failing)")
    backups_response = session.get(f"{FRONTEND_URL}/backups")
    print(f"Backups page response: {backups_response.status_code}")
    
    if backups_response.status_code == 200:
        print("✅ Backups page accessible")
    else:
        print("❌ Backups page access failed")
    
    # Step 6: Test API endpoints directly
    print_step("Testing API endpoints directly")
    api_devices_response = session.get(f"{FRONTEND_URL}/api/devices")
    print(f"API devices response: {api_devices_response.status_code}")
    
    if api_devices_response.status_code == 200:
        print("✅ API devices endpoint accessible")
        print(f"Devices: {json.dumps(api_devices_response.json(), indent=2)}")
    else:
        print("❌ API devices endpoint failed")
    
    print("\nAuthentication test complete!")

if __name__ == "__main__":
    main()
