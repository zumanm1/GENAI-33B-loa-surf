#!/usr/bin/env python3
"""
Comprehensive Authentication Test Runner for Net-Swift Orchestrator

This script:
1. Cleans up any existing server processes
2. Initializes the database to a clean state
3. Starts backend and frontend servers in the correct order
4. Runs backend API tests first to verify core functionality
5. Runs frontend end-to-end tests with Playwright
6. Provides detailed reporting of test results
7. Cleans up all processes on completion
"""

import os
import sys
import time
import signal
import subprocess
import argparse
import requests
import sqlite3
from pathlib import Path
import shutil

# Configuration
BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend_mock"
FRONTEND_DIR = BASE_DIR / "frontend_py"
DB_PATH = BACKEND_DIR / "network_automation.db"
DB_SCHEMA_PATH = BACKEND_DIR / "schema.sql"

# Server URLs and ports
BACKEND_URL = "http://localhost:5050"
FRONTEND_URL = "http://localhost:5006"
BACKEND_PORT = 5050
FRONTEND_PORT = 5006

# Test files
BACKEND_TEST_FILE = "test_auth_api.py"
FRONTEND_TEST_FILE = "test_auth_simple.py"

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(message):
    """Print a formatted header message."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")

def print_step(message):
    """Print a formatted step message."""
    print(f"{Colors.BLUE}{Colors.BOLD}[STEP]{Colors.ENDC} {message}")

def print_success(message):
    """Print a formatted success message."""
    print(f"{Colors.GREEN}{Colors.BOLD}[SUCCESS]{Colors.ENDC} {message}")

def print_warning(message):
    """Print a formatted warning message."""
    print(f"{Colors.YELLOW}{Colors.BOLD}[WARNING]{Colors.ENDC} {message}")

def print_error(message):
    """Print a formatted error message."""
    print(f"{Colors.RED}{Colors.BOLD}[ERROR]{Colors.ENDC} {message}")

def kill_process_by_port(port):
    """Kill any process using the specified port."""
    try:
        # Find process using the port
        result = subprocess.run(
            ["lsof", "-i", f":{port}", "-t"], 
            capture_output=True, 
            text=True
        )
        
        if result.stdout:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    print_step(f"Killing process {pid} using port {port}")
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        time.sleep(0.5)  # Give it time to terminate
                    except ProcessLookupError:
                        pass  # Process already gone
                    except Exception as e:
                        print_warning(f"Failed to kill process {pid}: {e}")
    except Exception as e:
        print_warning(f"Error checking for processes on port {port}: {e}")

def initialize_database():
    """Initialize the database to a clean state."""
    print_step("Initializing database to a clean state")
    
    # Backup existing database if it exists
    if DB_PATH.exists():
        backup_path = DB_PATH.with_suffix('.db.bak')
        shutil.copy2(DB_PATH, backup_path)
        print_step(f"Backed up existing database to {backup_path}")
    
    # Create a fresh database
    try:
        # Remove existing database
        if DB_PATH.exists():
            DB_PATH.unlink()
        
        # Create new database from schema
        conn = sqlite3.connect(str(DB_PATH))
        with open(str(DB_SCHEMA_PATH), 'r') as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()
        print_success("Database initialized successfully")
    except Exception as e:
        print_error(f"Failed to initialize database: {e}")
        sys.exit(1)

def start_server(script_path, port, name, env=None):
    """Start a server and return the process."""
    print_step(f"Starting {name} server on port {port}")
    
    # Environment variables
    process_env = os.environ.copy()
    if env:
        process_env.update(env)
    
    # Start the server
    process = subprocess.Popen(
        [sys.executable, str(script_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=process_env
    )
    
    return process

def wait_for_server(url, name, timeout=30, process=None):
    """Wait for a server to become available."""
    print_step(f"Waiting for {name} server to be ready (timeout: {timeout}s)")
    
    health_endpoint = f"{url}/api/health" if "backend" in name.lower() else url
    print_step(f"Checking health endpoint: {health_endpoint}")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        # Check if process is still running
        if process and process.poll() is not None:
            stdout, stderr = process.communicate()
            print_error(f"{name} server process terminated unexpectedly")
            print_error(f"STDOUT: {stdout.decode('utf-8', errors='replace') if stdout else 'None'}")
            print_error(f"STDERR: {stderr.decode('utf-8', errors='replace') if stderr else 'None'}")
            return False
            
        try:
            response = requests.get(health_endpoint, timeout=1)
            print_step(f"Health check response: {response.status_code}")
            if response.status_code == 200:
                print_success(f"{name} server is ready")
                return True
        except requests.exceptions.ConnectionError:
            print_step(f"Connection refused - {name} server not ready yet")
        except requests.exceptions.RequestException as e:
            print_step(f"Request error: {e}")
        
        # Print a dot to show progress
        print(".", end="", flush=True)
        time.sleep(1)
    
    print("\n")
    print_error(f"{name} server failed to start within {timeout} seconds")
    
    # Try to get server logs
    if process:
        try:
            stdout, stderr = process.communicate(timeout=1)
            print_error(f"Server logs:")
            print_error(f"STDOUT: {stdout.decode('utf-8', errors='replace') if stdout else 'None'}")
            print_error(f"STDERR: {stderr.decode('utf-8', errors='replace') if stderr else 'None'}")
        except:
            print_error("Could not retrieve server logs")
    
    return False

def run_tests(test_dir, test_file, name):
    """Run tests and return success status."""
    print_header(f"Running {name} tests")
    
    # Run the tests
    result = subprocess.run(
        [sys.executable, "-m", "pytest", test_file, "-v"],
        cwd=str(test_dir),
        capture_output=True,
        text=True
    )
    
    # Print test output
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    # Check if tests passed
    if result.returncode == 0:
        print_success(f"{name} tests passed")
        return True
    else:
        print_error(f"{name} tests failed")
        return False

def main():
    """Main function to run all tests."""
    parser = argparse.ArgumentParser(description="Run authentication tests for Net-Swift Orchestrator")
    parser.add_argument("--skip-backend", action="store_true", help="Skip backend tests")
    parser.add_argument("--skip-frontend", action="store_true", help="Skip frontend tests")
    parser.add_argument("--skip-db-init", action="store_true", help="Skip database initialization")
    args = parser.parse_args()
    
    print_header("Net-Swift Orchestrator Authentication Test Runner")
    
    # Step 1: Kill any existing server processes
    print_step("Cleaning up existing processes")
    kill_process_by_port(BACKEND_PORT)
    kill_process_by_port(FRONTEND_PORT)
    time.sleep(1)  # Give processes time to fully terminate
    
    # Step 2: Initialize database (unless skipped)
    if not args.skip_db_init:
        initialize_database()
    else:
        print_step("Skipping database initialization")
    
    # Step 3: Start backend server
    print_step("Starting backend server")
    backend_app_path = BACKEND_DIR / "app.py"
    if not backend_app_path.exists():
        print_error(f"Backend app not found at {backend_app_path}")
        sys.exit(1)
        
    backend_process = start_server(
        backend_app_path, 
        BACKEND_PORT, 
        "backend"
    )
    
    # Wait for backend to be ready with a longer timeout
    if not wait_for_server(BACKEND_URL, "backend", timeout=45, process=backend_process):
        print_error("Backend server failed to start properly. Terminating.")
        backend_process.terminate()
        sys.exit(1)
    
    # Step 4: Start frontend server
    print_step("Starting frontend server")
    frontend_app_path = FRONTEND_DIR / "app.py"
    if not frontend_app_path.exists():
        print_error(f"Frontend app not found at {frontend_app_path}")
        backend_process.terminate()
        sys.exit(1)
        
    frontend_process = start_server(
        frontend_app_path, 
        FRONTEND_PORT, 
        "frontend", 
        {"BACKEND_API_URL": BACKEND_URL}
    )
    
    # Wait for frontend to be ready
    if not wait_for_server(FRONTEND_URL, "frontend", timeout=30, process=frontend_process):
        print_error("Frontend server failed to start properly. Terminating.")
        backend_process.terminate()
        frontend_process.terminate()
        sys.exit(1)
    
    # Track test results
    backend_success = True
    frontend_success = True
    
    try:
        # Step 5: Run backend API tests
        if not args.skip_backend:
            backend_success = run_tests(BACKEND_DIR, BACKEND_TEST_FILE, "Backend API")
        else:
            print_step("Skipping backend tests")
        
        # Step 6: Run frontend end-to-end tests
        if not args.skip_frontend:
            frontend_success = run_tests(FRONTEND_DIR, FRONTEND_TEST_FILE, "Frontend End-to-End")
        else:
            print_step("Skipping frontend tests")
    
    finally:
        # Step 7: Clean up
        print_step("Cleaning up server processes")
        backend_process.terminate()
        frontend_process.terminate()
        
        # Give processes time to terminate gracefully
        time.sleep(1)
        
        # Force kill if still running
        try:
            backend_process.kill()
        except:
            pass
        
        try:
            frontend_process.kill()
        except:
            pass
    
    # Step 8: Print summary
    print_header("Test Summary")
    if not args.skip_backend:
        status = f"{Colors.GREEN}PASSED{Colors.ENDC}" if backend_success else f"{Colors.RED}FAILED{Colors.ENDC}"
        print(f"Backend API Tests: {status}")
    
    if not args.skip_frontend:
        status = f"{Colors.GREEN}PASSED{Colors.ENDC}" if frontend_success else f"{Colors.RED}FAILED{Colors.ENDC}"
        print(f"Frontend End-to-End Tests: {status}")
    
    # Exit with appropriate code
    if (args.skip_backend or backend_success) and (args.skip_frontend or frontend_success):
        print_success("All tests passed successfully!")
        return 0
    else:
        print_error("Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
