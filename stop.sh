#!/bin/bash
# Net-Swift Orchestrator Shutdown Script

# Text formatting
BOLD="\033[1m"
YELLOW="\033[0;33m"
NC="\033[0m" # No Color

PID_FILE=".pids"

echo -e "${BOLD}${YELLOW}Stopping all services...${NC}"

if [ ! -f "$PID_FILE" ]; then
    echo "PID file not found. Are the services running?"
    exit 1
fi

# Read PIDs and kill processes
while read -r pid; do
    if [ -n "$pid" ]; then
        echo "Stopping process with PID: $pid"
        kill $pid
    fi
done < "$PID_FILE"

# Remove the PID file
rm $PID_FILE

echo -e "${BOLD}${YELLOW}All services have been stopped.${NC}"
