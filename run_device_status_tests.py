#!/usr/bin/env python3
"""
Test runner for device status monitoring feature.
This script runs both backend and frontend tests for the device status monitoring feature.
"""
import os
import sys
import time
import subprocess
import signal
import requests
import shutil
import sqlite3
from pathlib import Path
import atexit

# Configuration
BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend_mock"
FRONTEND_DIR = BASE_DIR / "frontend_py"
DB_PATH = BACKEND_DIR / "network_automation.db"
DB_SCHEMA = BACKEND_DIR / "schema.sql"
DB_BACKUP = DB_PATH.with_suffix(".db.bak")

# Server URLs and ports
BACKEND_PORT = 5050
FRONTEND_PORT = 5006
BACKEND_URL = f"http://localhost:{BACKEND_PORT}"
FRONTEND_URL = f"http://localhost:{FRONTEND_PORT}"

# ANSI color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
UNDERLINE = "\033[4m"
END = "\033[0m"

# Track processes to clean up
processes_to_kill = []

def print_header(text):
    """Print a formatted header."""
    width = 80
    print("\n" + "=" * width)
    print(f"{text:^{width}}")
    print("=" * width + "\n")

def print_step(text):
    """Print a step in the process."""
    print(f"{BLUE}[STEP]{END} {text}")

def print_success(text):
    """Print a success message."""
    print(f"{GREEN}[SUCCESS]{END} {text}")

def print_error(text):
    """Print an error message."""
    print(f"{RED}[ERROR]{END} {text}")

def print_warning(text):
    """Print a warning message."""
    print(f"{YELLOW}[WARNING]{END} {text}")

def cleanup_processes():
    """Clean up any running processes."""
    print_step("Cleaning up server processes")
    for process in processes_to_kill:
        if process and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass

def kill_existing_processes():
    """Kill any existing processes on the backend and frontend ports."""
    print_step("Cleaning up existing processes")
    
    # Find and kill processes on backend port
    try:
        subprocess.run(
            f"lsof -i :{BACKEND_PORT} | grep LISTEN | awk '{{print $2}}' | xargs kill -9",
            shell=True, check=False
        )
    except:
        pass
    
    # Find and kill processes on frontend port
    try:
        subprocess.run(
            f"lsof -i :{FRONTEND_PORT} | grep LISTEN | awk '{{print $2}}' | xargs kill -9",
            shell=True, check=False
        )
    except:
        pass

def init_db():
    """Initialize the database to a clean state."""
    print_step("Initializing database to a clean state")
    
    # Backup existing database if it exists
    if DB_PATH.exists():
        shutil.copy2(DB_PATH, DB_BACKUP)
        print_step(f"Backed up existing database to {DB_BACKUP}")
        
        # Delete the existing database to start fresh
        DB_PATH.unlink()
    
    # Check if schema file exists
    if not DB_SCHEMA.exists():
        print_error(f"Schema file not found at {DB_SCHEMA}")
        sys.exit(1)
    
    # Create a fresh database
    conn = sqlite3.connect(DB_PATH)
    
    # Enable WAL mode and set busy timeout to reduce locking issues
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    
    try:
        # Execute schema file
        with open(DB_SCHEMA, 'r') as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
        conn.commit()
        
        # Add a test device with known status for testing
        conn.execute(
            "INSERT OR IGNORE INTO devices (name, host, port, status, device_type, platform) VALUES (?, ?, ?, ?, ?, ?)",
            ("TEST-DEVICE", "192.168.1.100", 23, "unknown", "cisco_ios_telnet", "ios")
        )
        conn.commit()
        
        print_success("Database initialized successfully")
    except sqlite3.Error as e:
        print_error(f"Database initialization error: {e}")
        sys.exit(1)
    finally:
        conn.close()

def start_server(app_path, port, name, env_vars=None):
    """Start a Flask server."""
    print_step(f"Starting {name} server on port {port}")
    
    # Set environment variables
    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)
    
    # Start the server
    process = subprocess.Popen(
        [sys.executable, str(app_path)],
        env=env,
        cwd=app_path.parent,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Register for cleanup
    processes_to_kill.append(process)
    
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
    """Run pytest tests."""
    print_header(f"Running {name} tests")
    
    # Run the tests
    result = subprocess.run(
        [sys.executable, "-m", "pytest", test_file, "-v"],
        cwd=test_dir,
        capture_output=True,
        text=True
    )
    
    # Print the output
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
    # Register cleanup handler
    atexit.register(cleanup_processes)
    
    print_header("Net-Swift Orchestrator Device Status Test Runner")
    
    # Step 1: Clean up existing processes
    kill_existing_processes()
    
    # Step 2: Initialize database
    init_db()
    
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
    
    # Step 5: Run backend tests
    backend_tests_passed = run_tests(
        BACKEND_DIR, 
        "test_device_status.py", 
        "Backend Device Status API"
    )
    
    # Step 6: Run frontend tests
    frontend_tests_passed = run_tests(
        FRONTEND_DIR, 
        "test_device_status.py", 
        "Frontend Device Status UI"
    )
    
    # Step 7: Run functional tests
    functional_tests_passed = run_tests(
        BASE_DIR, 
        "test_device_status_functional.py", 
        "Device Status Functional"
    )
    
    # Step 8: Print summary
    print_header("Test Summary")
    print(f"Backend Device Status API Tests: {GREEN}PASSED{END}" if backend_tests_passed else f"Backend Device Status API Tests: {RED}FAILED{END}")
    print(f"Frontend Device Status UI Tests: {GREEN}PASSED{END}" if frontend_tests_passed else f"Frontend Device Status UI Tests: {RED}FAILED{END}")
    print(f"Device Status Functional Tests: {GREEN}PASSED{END}" if functional_tests_passed else f"Device Status Functional Tests: {RED}FAILED{END}")
    
    if backend_tests_passed and frontend_tests_passed and functional_tests_passed:
        print_success("All tests passed successfully!")
        return 0
    else:
        print_error("Some tests failed. Please check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
