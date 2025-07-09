#!/bin/bash
# Test Environment Startup Script
# This script is specifically for starting services for tests (pytest, puppeteer)

# Set test mode explicitly
export RUN_MODE="TEST"
echo "Starting services in TEST mode with mock AI service"

# Call the regular start script with TEST mode
bash start.sh

# Exit with the same status as the start script
exit $?
