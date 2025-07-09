#!/bin/bash
# Net-Swift Orchestrator Startup Script
# This script ensures clean port initialization before starting services
# It will:
# 1. Clean up any processes using the required ports
# 2. Start backend, frontend, and AI services with production configuration
# 3. Verify all services are healthy

# Text formatting
BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

echo -e "${BOLD}=== Net-Swift Orchestrator Startup ===${NC}"

# Set environment variables
export BACKEND_URL="http://127.0.0.1:5050"
export FRONTEND_URL="http://127.0.0.1:5051"
export AI_AGENT_URL="http://127.0.0.1:5004"

# Ensure we're in the project root directory
cd "$(dirname "$0")"

# Define critical ports
BACKEND_PORT=5050
FRONTEND_PORT=5051
AI_PORT=5004

# Function to check and clean ports
cleanup_ports() {
    echo -e "\n${BOLD}${YELLOW}Cleaning up service ports...${NC}"
    
    # Check if our port manager utility is available
    if [ -f "utils/port_manager.py" ]; then
        echo "Using port_manager.py utility"
        python utils/port_manager.py free ${BACKEND_PORT} ${FRONTEND_PORT} ${AI_PORT} --force
        if [ $? -ne 0 ]; then
            echo -e "${RED}Failed to clean up ports with port_manager.py${NC}"
            return 1
        fi
    else
        echo "Port manager utility not found, using fallback method"
        
        # Cleanup each port manually
        for PORT in ${BACKEND_PORT} ${FRONTEND_PORT} ${AI_PORT}; do
            echo -e "Checking port ${PORT}..."
            
            # Find processes using this port
            PIDS=$(lsof -i:${PORT} -t 2>/dev/null)
            
            if [ -n "$PIDS" ]; then
                echo -e "${YELLOW}Port ${PORT} is in use by process(es): ${PIDS}${NC}"
                echo "Killing processes..."
                
                for PID in $PIDS; do
                    echo "Killing process ${PID}..."
                    kill -9 $PID 2>/dev/null
                    if [ $? -eq 0 ]; then
                        echo "Process ${PID} terminated"
                    else
                        echo -e "${RED}Failed to kill process ${PID}${NC}"
                    fi
                done
            else
                echo -e "${GREEN}Port ${PORT} is available${NC}"
            fi
        done
    fi
    
    echo -e "${GREEN}Port cleanup complete${NC}"
    return 0
}

# Function to start backend service
start_backend() {
    echo -e "\n${BOLD}Starting backend service on port ${BACKEND_PORT}...${NC}"
    
    # Navigate to backend directory
    cd backend
    
    # Start with gunicorn for production-grade stability
    gunicorn --bind 0.0.0.0:${BACKEND_PORT} --workers 4 'app:app' &
    BACKEND_PID=$!
    
    cd ..
    echo -e "${GREEN}Backend started with PID ${BACKEND_PID}${NC}"
}

# Function to start frontend service
start_frontend() {
    echo -e "\n${BOLD}Starting frontend service on port ${FRONTEND_PORT}...${NC}"
    
    # Navigate to frontend directory
    cd frontend_py
    
    # Start with gunicorn for production-grade stability
    gunicorn --bind 0.0.0.0:${FRONTEND_PORT} --workers 4 'app:app' &
    FRONTEND_PID=$!
    
    cd ..
    echo -e "${GREEN}Frontend started with PID ${FRONTEND_PID}${NC}"
}

# Function to start AI service
start_ai() {
    echo -e "\n${BOLD}Starting AI service on port ${AI_PORT}...${NC}"
    
    # Navigate to AI service directory
    cd ai_service
    
    # Start AI service
    python app.py &
    AI_PID=$!
    
    cd ..
    echo -e "${GREEN}AI service started with PID ${AI_PID}${NC}"
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
