#!/usr/bin/env python
"""
Port Management Utility

This script provides functions to manage port availability and process cleanup
to prevent zombie processes and port conflicts in the Net-Swift Orchestrator.

Usage:
  - Before starting services: ensure_ports_available([5050, 5051, 5052])
  - During test teardown: cleanup_service_processes()
"""

import os
import signal
import subprocess
import time
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("port_manager")

def get_processes_on_port(port):
    """
    Get list of process IDs using the specified port.
    
    Args:
        port (int): Port number to check
        
    Returns:
        list: List of process IDs (integers) using the port
    """
    try:
        # Using lsof to find processes using the port
        cmd = f"lsof -i:{port} -t"
        result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        if result.returncode != 0 and not result.stdout.strip():
            return []
            
        # Parse process IDs from output
        pids = [int(pid) for pid in result.stdout.strip().split('\n') if pid]
        return pids
    except Exception as e:
        logger.error(f"Error getting processes on port {port}: {e}")
        return []

def kill_process(pid, force=False):
    """
    Kill a process by its PID.
    
    Args:
        pid (int): Process ID to kill
        force (bool): Whether to use SIGKILL (-9) instead of SIGTERM
        
    Returns:
        bool: True if process was killed successfully
    """
    try:
        sig = signal.SIGKILL if force else signal.SIGTERM
        os.kill(pid, sig)
        logger.info(f"Sent {'SIGKILL' if force else 'SIGTERM'} to process {pid}")
        
        # Give process time to terminate
        time.sleep(0.5)
        
        # Check if process still exists
        try:
            os.kill(pid, 0)  # This will raise an error if process doesn't exist
            if force:
                logger.warning(f"Process {pid} still exists after SIGKILL")
                return False
            else:
                # Process didn't terminate with SIGTERM, try SIGKILL
                logger.warning(f"Process {pid} didn't terminate with SIGTERM, using SIGKILL")
                return kill_process(pid, force=True)
        except OSError:
            # Process doesn't exist anymore
            return True
    except ProcessLookupError:
        logger.info(f"Process {pid} doesn't exist")
        return True
    except Exception as e:
        logger.error(f"Error killing process {pid}: {e}")
        return False

def ensure_port_available(port, force=False):
    """
    Ensure a port is available by terminating processes using it if necessary.
    
    Args:
        port (int): Port number to check/free
        force (bool): Whether to use SIGKILL immediately instead of trying SIGTERM first
        
    Returns:
        bool: True if port is now available, False otherwise
    """
    pids = get_processes_on_port(port)
    
    if not pids:
        logger.info(f"Port {port} is already available")
        return True
        
    logger.warning(f"Found {len(pids)} processes using port {port}: {pids}")
    
    # Kill each process
    success = True
    for pid in pids:
        if not kill_process(pid, force=force):
            success = False
            
    # Verify port is now available
    remaining_pids = get_processes_on_port(port)
    if remaining_pids:
        logger.error(f"Failed to free port {port}, processes still using it: {remaining_pids}")
        return False
    else:
        logger.info(f"Successfully freed port {port}")
        return True

def ensure_ports_available(ports, force=False):
    """
    Ensure multiple ports are available.
    
    Args:
        ports (list): List of port numbers to check/free
        force (bool): Whether to use SIGKILL immediately
        
    Returns:
        bool: True if all ports are now available
    """
    success = True
    for port in ports:
        if not ensure_port_available(port, force=force):
            success = False
            
    return success

def find_service_processes():
    """
    Find all processes that might be related to our services.
    
    Returns:
        list: List of process IDs likely belonging to our services
    """
    service_pids = []
    
    # Key patterns in command line that identify our service processes
    patterns = [
        "backend/app.py", 
        "frontend_py/app.py",
        "mock_ai_service.py",
        "gunicorn.*5050",
        "gunicorn.*5051",
        "gunicorn.*5052"
    ]
    
    try:
        for pattern in patterns:
            cmd = f"ps aux | grep '{pattern}' | grep -v grep | awk '{{print $2}}'"
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            pids = [int(pid) for pid in result.stdout.strip().split('\n') if pid]
            service_pids.extend(pids)
    except Exception as e:
        logger.error(f"Error finding service processes: {e}")
    
    return list(set(service_pids))  # Remove duplicates

def cleanup_service_processes(force=True):
    """
    Cleanup all processes related to our services.
    
    Args:
        force (bool): Whether to use SIGKILL immediately
        
    Returns:
        bool: True if cleanup was successful
    """
    service_pids = find_service_processes()
    
    if not service_pids:
        logger.info("No service processes found to clean up")
        return True
        
    logger.info(f"Found {len(service_pids)} service processes to clean up: {service_pids}")
    
    # Kill each service process
    success = True
    for pid in service_pids:
        if not kill_process(pid, force=force):
            success = False
    
    # Verify ports are available
    service_ports = [5050, 5051, 5052]
    for port in service_ports:
        pids = get_processes_on_port(port)
        if pids:
            logger.error(f"Port {port} still in use after cleanup by processes: {pids}")
            success = False
            
    return success

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage port availability and process cleanup")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Check port command
    check_parser = subparsers.add_parser("check", help="Check if ports are available")
    check_parser.add_argument("ports", type=int, nargs="+", help="Port numbers to check")
    
    # Free port command
    free_parser = subparsers.add_parser("free", help="Free up ports by terminating processes")
    free_parser.add_argument("ports", type=int, nargs="+", help="Port numbers to free")
    free_parser.add_argument("--force", action="store_true", help="Use SIGKILL immediately")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up all service processes")
    cleanup_parser.add_argument("--force", action="store_true", help="Use SIGKILL immediately")
    
    args = parser.parse_args()
    
    if args.command == "check":
        for port in args.ports:
            pids = get_processes_on_port(port)
            if pids:
                print(f"Port {port} is in use by processes: {pids}")
            else:
                print(f"Port {port} is available")
    elif args.command == "free":
        ensure_ports_available(args.ports, force=args.force)
    elif args.command == "cleanup":
        cleanup_service_processes(force=args.force)
    else:
        parser.print_help()
