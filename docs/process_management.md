# Net-Swift Orchestrator: Process Management & Port Conflict Resolution

## Table of Contents
1. [Introduction](#introduction)
2. [Root Cause Analysis](#root-cause-analysis)
3. [Resolution Process](#resolution-process)
4. [New Safeguards](#new-safeguards)
5. [Usage Guide](#usage-guide)
6. [Troubleshooting](#troubleshooting)

## Introduction

This document provides a comprehensive guide on managing process conflicts and port availability within the Net-Swift Orchestrator system. It addresses a critical issue where zombie processes would hold required ports (5050, 5051) without responding to requests, causing service health checks to fail and preventing new service instances from starting.

## Root Cause Analysis

### The Problem

During testing and validation of the port migration, we encountered persistent service health check failures. Despite killing processes and attempting to restart services, tests would consistently fail with connection timeouts when checking service health.

### Investigation

Through systematic analysis, we identified the following issues:

1. **Zombie Python Processes**: Previous test runs left Python processes running in the background that continued to hold ports 5050 (backend) and 5051 (frontend).

2. **Deadlock Condition**: These processes were holding the ports but not responding to requests, creating a deadlock where:
   - Health checks timed out against unresponsive processes
   - New service instances couldn't start because ports were already in use
   - Test framework failed due to service unavailability

3. **Ineffective Process Management**: Standard process termination (`kill`) was insufficient as some processes required force termination (`kill -9`).

4. **Missing Port Validation**: The system lacked a mechanism to verify port availability before attempting to start services.

## Resolution Process

We implemented a systematic approach to resolve the port conflicts:

### 1. Identify Processes on Critical Ports

```bash
# Find processes using specific ports
lsof -i:5050
lsof -i:5051
```

This revealed multiple Python processes holding these ports but not responding to requests.

### 2. Force Terminate Processes

```bash
# Force kill processes using SIGKILL
kill -9 <PID1> <PID2>
```

The standard SIGTERM signal was insufficient; SIGKILL (-9) was required to forcefully terminate the zombie processes.

### 3. Verify Port Availability

```bash
# Check if ports are now available
lsof -i:5050 || echo "Port 5050 is available"
lsof -i:5051 || echo "Port 5051 is available"
```

This confirmed the ports were truly free before attempting to start services.

### 4. Deploy Production-Grade Services

```bash
# Start backend with gunicorn
cd /path/to/backend && gunicorn --bind 0.0.0.0:5050 --workers 4 'app:app'

# Start frontend with gunicorn
cd /path/to/frontend_py && gunicorn --bind 0.0.0.0:5051 --workers 4 'app:app'
```

Using `gunicorn` with multiple workers provided better stability and performance than development servers.

### 5. Validate Service Health

```bash
# Check backend health
curl -s http://127.0.0.1:5050/api/health

# Check frontend health
curl -s -I http://127.0.0.1:5051/login
```

This verified that services were responding correctly after restart.

### 6. Execute Tests

```bash
# Run the health check script first
./tests/wait_for_services.sh

# Run tests after confirming all services are healthy
python -m pytest tests/test_smoke.py -v
```

With all services properly running, tests executed successfully.

## New Safeguards

To prevent these issues in the future, we've implemented several safeguards:

### 1. Port Management Utility

A dedicated `port_manager.py` utility provides functions to:
- Check port availability before starting services
- Identify and terminate processes holding specific ports
- Perform cleanup of service processes

### 2. Enhanced Test Fixtures

The pytest configuration in `conftest.py` has been enhanced to:
- Verify port availability before tests begin
- Automatically free ports if they're held by zombie processes
- Clean up processes after test completion
- Provide better error reporting for service unavailability

### 3. Shell-Based Health Check Script

A curl-based health check script (`wait_for_services.sh`) provides:
- Lightweight service validation without Python dependencies
- Isolation from the test environment to prevent resource conflicts
- Clear reporting of service health status

## Usage Guide

### Using the Port Manager Utility

```python
# Import the utility
from utils.port_manager import ensure_ports_available, cleanup_service_processes

# Check and free specific ports if needed
ensure_ports_available([5050, 5051, 5052], force=True)

# Clean up all service processes
cleanup_service_processes(force=True)
```

You can also use the utility from the command line:

```bash
# Check if ports are available
python -m utils.port_manager check 5050 5051 5052

# Free specific ports
python -m utils.port_manager free 5050 5051 5052 --force

# Clean up all service processes
python -m utils.port_manager cleanup --force
```

### Test Execution Best Practices

1. **Always start with port validation**:
   ```bash
   python -m utils.port_manager check 5050 5051 5052
   ```

2. **Clean up before starting services**:
   ```bash
   python -m utils.port_manager cleanup --force
   ```

3. **Validate services after startup**:
   ```bash
   ./tests/wait_for_services.sh
   ```

4. **Only then run tests**:
   ```bash
   python -m pytest tests/test_smoke.py -v
   ```

## Troubleshooting

### Services Won't Start

If services fail to start with "Address already in use" errors:

1. Check for processes using the required ports:
   ```bash
   lsof -i:5050
   lsof -i:5051
   ```

2. Force terminate any processes found:
   ```bash
   kill -9 <PID>
   ```

3. If the port manager utility is available:
   ```bash
   python -m utils.port_manager free 5050 5051 --force
   ```

### Health Checks Failing

If health checks fail despite services appearing to start:

1. Check if the services are truly running:
   ```bash
   ps aux | grep gunicorn
   ```

2. Restart the services with direct console output:
   ```bash
   cd /path/to/backend && python app.py
   ```

3. Check for any startup errors or exceptions

4. Verify network configuration allows connections to the service ports

### Tests Failing Despite Services Running

1. Run the health check script to validate all services:
   ```bash
   ./tests/wait_for_services.sh
   ```

2. Check service logs for errors or warnings:
   ```bash
   cat backend.log
   cat frontend.log
   ```

3. Verify the test environment variables match the actual service ports:
   ```bash
   echo $BACKEND_URL $FRONTEND_URL $AI_AGENT_URL
   ```

4. Try running a minimal test case to isolate the issue:
   ```bash
   python -m pytest tests/test_smoke.py::test_backend_devices -v
   ```
