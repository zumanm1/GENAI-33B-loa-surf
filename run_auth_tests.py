"""
Script to run authentication tests systematically.
This script will:
1. Start the backend server
2. Run backend API tests
3. Start the frontend server
4. Run frontend end-to-end tests
"""
import subprocess
import time
import os
import sys
import requests
from pathlib import Path

# Project directories
BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend_mock"
FRONTEND_DIR = BASE_DIR / "frontend_py"

def wait_for_server(url, max_retries=10, retry_delay=1):
    """Wait for a server to be available."""
    print(f"Waiting for server at {url}...")
    for i in range(max_retries):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print(f"Server at {url} is up and running!")
                return True
        except requests.exceptions.ConnectionError:
            print(f"Attempt {i+1}/{max_retries}: Server not available yet, retrying in {retry_delay}s...")
            time.sleep(retry_delay)
    
    print(f"Failed to connect to server at {url} after {max_retries} attempts")
    return False

def start_backend_server():
    """Start the backend server."""
    print("Starting backend server...")
    os.chdir(BACKEND_DIR)
    
    # Start the backend server as a subprocess
    backend_process = subprocess.Popen(
        ["python3", "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for the backend server to be available
    if wait_for_server("http://localhost:5050/api/health"):
        print("Backend server started successfully!")
        return backend_process
    else:
        print("Failed to start backend server")
        backend_process.terminate()
        return None

def start_frontend_server():
    """Start the frontend server."""
    print("Starting frontend server...")
    os.chdir(FRONTEND_DIR)
    
    # Start the frontend server as a subprocess
    frontend_process = subprocess.Popen(
        ["python3", "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for the frontend server to be available
    if wait_for_server("http://localhost:5006"):
        print("Frontend server started successfully!")
        return frontend_process
    else:
        print("Failed to start frontend server")
        frontend_process.terminate()
        return None

def run_backend_tests():
    """Run backend authentication API tests."""
    print("\n=== Running Backend Authentication API Tests ===\n")
    os.chdir(BACKEND_DIR)
    
    # Run the backend API tests
    result = subprocess.run(
        ["python3", "-m", "pytest", "test_auth_api.py", "-v"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    return result.returncode == 0

def run_frontend_tests():
    """Run frontend end-to-end tests."""
    print("\n=== Running Frontend End-to-End Tests ===\n")
    os.chdir(FRONTEND_DIR)
    
    # Run the frontend end-to-end tests
    result = subprocess.run(
        ["python3", "-m", "pytest", "test_auth_simple.py", "-v"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    return result.returncode == 0

def main():
    """Main function to run all tests."""
    print("=== Authentication Testing Suite ===")
    
    # Start the backend server
    backend_process = start_backend_server()
    if not backend_process:
        print("Exiting due to backend server startup failure")
        return 1
    
    # Run backend tests
    backend_tests_passed = run_backend_tests()
    
    # Start the frontend server
    frontend_process = start_frontend_server()
    if not frontend_process:
        print("Exiting due to frontend server startup failure")
        backend_process.terminate()
        return 1
    
    # Run frontend tests
    frontend_tests_passed = run_frontend_tests()
    
    # Clean up
    print("\n=== Cleaning Up ===")
    backend_process.terminate()
    frontend_process.terminate()
    
    # Report results
    print("\n=== Test Results ===")
    print(f"Backend API Tests: {'PASSED' if backend_tests_passed else 'FAILED'}")
    print(f"Frontend End-to-End Tests: {'PASSED' if frontend_tests_passed else 'FAILED'}")
    
    return 0 if backend_tests_passed and frontend_tests_passed else 1

if __name__ == "__main__":
    sys.exit(main())
