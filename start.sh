#!/bin/bash
# Net-Swift Orchestrator Startup Script

# Text formatting
BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

echo -e "${BOLD}=== Net-Swift Orchestrator Startup ===${NC}"

# Ensure we're in the project root directory
cd "$(dirname "$0")"

# Install dependencies
echo -e "\n${BOLD}${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install dependencies. Aborting.${NC}"
    exit 1
fi
echo -e "${GREEN}Dependencies installed successfully.${NC}"

# Define ports and PID file
BACKEND_PORT=5050
FRONTEND_PORT=5051
AI_PORT=5052
PID_FILE=".pids"

# Function to clean up ports
cleanup_ports() {
    echo -e "\n${BOLD}${YELLOW}Cleaning up service ports...${NC}"
    for PORT in ${BACKEND_PORT} ${FRONTEND_PORT} ${AI_PORT}; do
        echo "Checking port $PORT..."
        # Use xargs to handle multiple PIDs on the same port
        lsof -t -i:$PORT | xargs -r kill -9
    done
    echo -e "${GREEN}Ports cleaned successfully.${NC}"
}

# Clean up ports before starting
cleanup_ports

# Clean up old database to ensure a fresh start
rm -f backend/network_automation.db

# Start services
echo -e "\n${BOLD}${YELLOW}Starting services...${NC}"

# Start Backend
gunicorn --chdir backend --bind 0.0.0.0:${BACKEND_PORT} --workers 1 --threads 8 app:app & 
BACKEND_PID=$!
echo "- Backend started on port ${BACKEND_PORT} with PID ${BACKEND_PID}"

# Start Frontend
gunicorn --chdir frontend_py --bind 0.0.0.0:${FRONTEND_PORT} --workers 1 app:app &
FRONTEND_PID=$!
echo "- Frontend started on port ${FRONTEND_PORT} with PID ${FRONTEND_PID}"

# Start AI Service
gunicorn --chdir ai_service --bind 0.0.0.0:${AI_PORT} --workers 1 app:app &
AI_PID=$!
echo "- AI Service started on port ${AI_PORT} with PID ${AI_PID}"

# Save PIDs to file
# Overwrite PID file with the new PIDs
> $PID_FILE
echo $BACKEND_PID >> $PID_FILE
echo $FRONTEND_PID >> $PID_FILE
echo $AI_PID >> $PID_FILE

echo -e "\n${GREEN}All services are running.${NC}"
echo -e "To stop all services, run ${BOLD}./stop.sh${NC}"

# Function to start AI service
start_ai() {
    echo -e "\n${BOLD}Starting AI service on port ${AI_PORT}...${NC}"
    
    # Get the base directory
    BASE_DIR="$(pwd)"
    
    # Start AI service based on RUN_MODE
    if [ "$RUN_MODE" = "PRODUCTION" ]; then
        echo "Running in PRODUCTION mode, using real AI service"
        cd "$BASE_DIR/ai_service"
        
        # Use gunicorn for production-grade stability
        gunicorn --bind 0.0.0.0:${AI_PORT} --workers 2 'app:app' &
        AI_PID=$!
        
        cd "$BASE_DIR"
        echo -e "${GREEN}AI service (real) started with PID ${AI_PID}${NC}"
    else
        echo "Running in TEST mode, using mock AI service"
        cd "$BASE_DIR/backend_mock"
        
        # Start mock AI service
        python mock_ai_service.py &
        AI_PID=$!
        
        cd "$BASE_DIR"
        echo -e "${GREEN}AI service (mock) started with PID ${AI_PID}${NC}"
    fi
}

# Function to check service health
check_health() {
    echo -e "\n${BOLD}Verifying service health...${NC}"
    
    # Use wait_for_services script if available
    if [ -f "tests/wait_for_services.sh" ]; then
        echo "Using wait_for_services.sh script"
        bash tests/wait_for_services.sh
        return $?
    else
        # Manual health checks
        echo "Health check script not found, performing manual checks"
        
        # Backend health check
        echo "Checking backend health..."
        curl -s ${BACKEND_URL}/api/health -o /dev/null
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Backend health check passed${NC}"
        else
            echo -e "${RED}Backend health check failed${NC}"
            return 1
        fi
        
        # Frontend health check
        echo "Checking frontend health..."
        curl -s -I ${FRONTEND_URL}/login | head -n 1 | grep "200"
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Frontend health check passed${NC}"
        else
            echo -e "${RED}Frontend health check failed${NC}"
            return 1
        fi
        
        # AI service health check
        echo "Checking AI service health..."
        curl -s ${AI_AGENT_URL}/health -o /dev/null
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}AI service health check passed${NC}"
        else
            echo -e "${RED}AI service health check failed${NC}"
            return 1
        fi
        
        echo -e "${GREEN}All services healthy${NC}"
        return 0
    fi
}

# Main execution flow
main() {
    # Cleanup existing processes
    cleanup_ports
    if [ $? -ne 0 ]; then
        echo -e "${RED}Port cleanup failed. Please check processes manually.${NC}"
        exit 1
    fi
    
    # Start all services
    start_backend
    start_frontend
    start_ai
    
    # Wait for services to initialize
    echo -e "\n${YELLOW}Waiting for services to initialize (5 seconds)...${NC}"
    sleep 5
    
    # Check service health
    check_health
    if [ $? -ne 0 ]; then
        echo -e "${RED}Service health check failed. Please check logs for details.${NC}"
        exit 1
    fi
    
    echo -e "\n${BOLD}${GREEN}Net-Swift Orchestrator started successfully!${NC}"
    echo -e "Backend: ${BACKEND_URL}"
    echo -e "Frontend: ${FRONTEND_URL}"
    echo -e "AI Service: ${AI_AGENT_URL}"
    echo -e "\nPress Ctrl+C to stop all services"
    
    # Wait for user interrupt
    wait
}

# Run main function
main
