"""Pytest configuration that assumes the system services are already running.

This file replaces the auto-spawning fixture that previously tried to start
new backend / frontend processes on the same ports, which caused port-in-use
errors during the smoke tests.  Instead we simply verify that the expected
services are reachable and skip the tests gracefully if not.

Enhanced with port management utilities to prevent zombie processes and port conflicts.
"""

import os
import time
import sys
import logging
import subprocess
import pytest
import requests

# Add project root to path so we can import our utility modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the port manager utility if available, otherwise define a fallback
try:
    from utils.port_manager import ensure_ports_available, cleanup_service_processes
    PORT_MANAGER_AVAILABLE = True
except ImportError:
    PORT_MANAGER_AVAILABLE = False
    print("WARNING: port_manager utility not found, using fallback process management")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_fixtures")

# Service URLs
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:5050")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5051")
AI_URL = os.getenv("AI_AGENT_URL", "http://127.0.0.1:5052")

# Health check endpoints
BACKEND_HEALTH = f"{BACKEND_URL}/api/health"
FRONTEND_HEALTH = f"{FRONTEND_URL}/login"
AI_HEALTH = f"{AI_URL}/health"

# Timeouts
_TIMEOUT = 30
_HEALTH_CHECK_TIMEOUT = 10

# Extract port numbers from URLs
def _extract_port(url):
    """Extract port number from URL"""
    import re
    match = re.search(r":(\d+)", url)
    if match:
        return int(match.group(1))
    return None

SERVICE_PORTS = [
    _extract_port(BACKEND_URL),
    _extract_port(FRONTEND_URL), 
    _extract_port(AI_URL)
]
SERVICE_PORTS = [p for p in SERVICE_PORTS if p is not None]

def _is_up(url: str) -> bool:
    """Check if a service is responding at the given URL"""
    print(f"Health checking: {url}...")
    try:
        r = requests.get(url, timeout=_HEALTH_CHECK_TIMEOUT)
        if r.status_code == 200:
            print(f"  -> SUCCESS ({r.status_code})")
            return True
        else:
            print(f"  -> FAIL ({r.status_code})")
            return False
    except requests.RequestException as e:
        print(f"  -> FAIL (Exception: {e})")
        return False

def _fallback_ensure_ports_available():
    """Fallback implementation if port_manager utility is not available"""
    success = True
    for port in SERVICE_PORTS:
        try:
            # Check if port is in use using lsof
            result = subprocess.run(
                f"lsof -i:{port} -t", 
                shell=True, 
                text=True,
                capture_output=True
            )
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                print(f"WARNING: Port {port} is in use by processes: {pids}")
                
                # Try to kill the processes
                for pid in pids:
                    if pid.strip():
                        print(f"Attempting to kill process {pid}...")
                        try:
                            subprocess.run(f"kill -9 {pid}", shell=True, check=True)
                            print(f"Successfully killed process {pid}")
                        except subprocess.SubprocessError as e:
                            print(f"Failed to kill process {pid}: {e}")
                            success = False
            else:
                print(f"Port {port} is available")
        except Exception as e:
            print(f"Error checking port {port}: {e}")
            success = False
            
    return success

def _check_services_health():
    """Check if all required services are healthy"""
    services_health = {
        "backend": _is_up(BACKEND_HEALTH),
        "frontend": _is_up(FRONTEND_HEALTH),
        "ai": _is_up(AI_HEALTH)
    }
    return services_health

@pytest.fixture(scope="session", autouse=True)
def verify_service_ports():
    """Session-level fixture that
    1. Ensures required ports are free
    2. Starts the application services (if they are not already running)
    3. Registers teardown logic to kill the spawned PIDs and free the ports again
    """
    import re
    import shlex

    print("\n=== Verifying service ports availability ===")

    # 1) Ensure ports are free (kill zombies)
    if PORT_MANAGER_AVAILABLE:
        ports_available = ensure_ports_available(SERVICE_PORTS, force=True)
    else:
        ports_available = _fallback_ensure_ports_available()

    if not ports_available:
        pytest.exit("Failed to free required ports. Manually kill processes and try again.")

    # 2) Health-check existing services
    services_ok = all(_check_services_health().values())
    spawned_pids = []

    if not services_ok:
        print("Services not running – invoking start_services.sh …")
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'start_services.sh'))
        try:
            # Run the script synchronously and capture its output (it backgrounds services and exits)
            result = subprocess.run([script_path], text=True, capture_output=True, check=True)
            print(result.stdout)

            # Parse the PID line e.g. "kill 123 456 789"
            match = re.search(r"kill\s+([0-9\s]+)", result.stdout)
            if match:
                spawned_pids = [pid for pid in match.group(1).strip().split() if pid.isdigit()]
                print(f"Captured service PIDs: {spawned_pids}")
            else:
                print("WARNING: Could not parse PIDs from start_services.sh output; teardown will rely on port cleanup only.")

        except subprocess.CalledProcessError as e:
            pytest.exit(f"Failed to run start_services.sh: {e.stderr}")

        # Re-check health with a more generous back-off
        print("Waiting for services to become healthy...")
        for i in range(45):  # Increased timeout to 45s
            health_status = _check_services_health()
            if all(health_status.values()):
                print("All services are healthy!")
                break
            print(f"Attempt {i+1}/45: Waiting... Current status: {health_status}")
            time.sleep(1)
        else:
            pytest.exit("Services failed to become healthy in time after starting.")
    else:
        print("Existing services are healthy – reuse alive instances.")

    # Yield control to the tests
    yield

    # 3) Teardown – kill spawned services and free ports
    print("\n=== Cleaning up after tests ===")
    if spawned_pids:
        print(f"Killing spawned service PIDs: {spawned_pids}")
        subprocess.run(["kill", "-9", *spawned_pids], text=True, check=False)
        time.sleep(1)

    # Final port sweep
    if PORT_MANAGER_AVAILABLE:
        ensure_ports_available(SERVICE_PORTS, force=True)
    else:
        _fallback_ensure_ports_available()

@pytest.fixture(scope="session")
def services_health():
    """
    Check if all required services are healthy.
    Skip tests if services are not available.
    """
    health_status = _check_services_health()
    
    # Require all services to be healthy
    all_healthy = all(health_status.values())
    
    if not all_healthy:
        unhealthy = [name for name, status in health_status.items() if not status]
        pytest.exit(f"Required services are not running on expected ports. Start the stack before executing tests.")
    
    return health_status



