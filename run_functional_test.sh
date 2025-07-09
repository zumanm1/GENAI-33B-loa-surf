#!/bin/bash
# Net-Swift Orchestrator - Functional Test Runner
# This script manages the complete lifecycle of functional testing:
# 1. Kills any existing processes on test ports
# 2. Sets up test environment with mock AI service
# 3. Runs functional tests with Puppeteer
# 4. Performs proper cleanup

# Text formatting
BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

echo -e "${BOLD}=== Net-Swift Orchestrator Functional Test Runner ===${NC}"

# Define critical ports
BACKEND_PORT=5050
FRONTEND_PORT=5051
AI_PORT=5004

# Function to check and clean ports
cleanup_ports() {
    echo -e "${BOLD}${YELLOW}Cleaning up service ports...${NC}"
    
    # Check for processes using our ports
    echo "Checking for processes using ports ${BACKEND_PORT}, ${FRONTEND_PORT}, and ${AI_PORT}..."
    
    # Find processes using our ports
    lsof -i :${BACKEND_PORT},${FRONTEND_PORT},${AI_PORT} | grep LISTEN
    
    # Kill processes using backend port
    echo "Cleaning up port ${BACKEND_PORT}..."
    lsof -t -i :${BACKEND_PORT} | xargs -r kill -9
    
    # Kill processes using frontend port
    echo "Cleaning up port ${FRONTEND_PORT}..."
    lsof -t -i :${FRONTEND_PORT} | xargs -r kill -9
    
    # Kill processes using AI port
    echo "Cleaning up port ${AI_PORT}..."
    lsof -t -i :${AI_PORT} | xargs -r kill -9
    
    echo "Verifying ports are free..."
    sleep 2
    BACKEND_USED=$(lsof -i :${BACKEND_PORT} | grep LISTEN | wc -l)
    FRONTEND_USED=$(lsof -i :${FRONTEND_PORT} | grep LISTEN | wc -l)
    AI_USED=$(lsof -i :${AI_PORT} | grep LISTEN | wc -l)
    
    if [ ${BACKEND_USED} -gt 0 ] || [ ${FRONTEND_USED} -gt 0 ] || [ ${AI_USED} -gt 0 ]; then
        echo -e "${RED}Some ports are still in use after cleanup!${NC}"
        echo "Running aggressive process cleanup..."
        pkill -f "gunicorn.*${BACKEND_PORT}"
        pkill -f "gunicorn.*${FRONTEND_PORT}"
        pkill -f "python.*${AI_PORT}"
        sleep 1
    fi
    
    echo -e "${GREEN}Ports cleaned successfully${NC}"
}

# Function to set up the test environment
setup_test_env() {
    echo -e "\n${BOLD}${GREEN}Setting up test environment...${NC}"
    
    # Create admin user if needed
    if [ -f "backend/create_admin.py" ]; then
        echo "Ensuring admin user exists in database..."
        cd backend
        python create_admin.py
        cd ..
    fi
    
    # Start services in TEST mode
    echo "Starting services in TEST mode..."
    export RUN_MODE="TEST"
    ./start_test_env.sh
    
    # Wait for services to be ready
    echo "Waiting for services to be ready..."
    for i in {1..10}; do
        SERVICES_READY=0
        
        # Check backend
        if curl -s http://localhost:${BACKEND_PORT}/api/health > /dev/null; then
            SERVICES_READY=$((SERVICES_READY+1))
        fi
        
        # Check frontend
        if curl -s http://localhost:${FRONTEND_PORT}/login -I | grep -q "200 OK"; then
            SERVICES_READY=$((SERVICES_READY+1))
        fi
        
        # Check AI service
        if curl -s http://localhost:${AI_PORT}/health > /dev/null; then
            SERVICES_READY=$((SERVICES_READY+1))
        fi
        
        if [ ${SERVICES_READY} -eq 3 ]; then
            echo -e "${GREEN}All services are ready!${NC}"
            break
        fi
        
        echo "Waiting for services... (${i}/10)"
        sleep 3
    done
}

# Function to run Puppeteer functional tests
run_functional_tests() {
    echo -e "\n${BOLD}${GREEN}Running functional tests with Puppeteer...${NC}"
    
    # Check if we have node and required packages
    if ! command -v node > /dev/null; then
        echo -e "${RED}Node.js is not installed. Cannot run Puppeteer tests.${NC}"
        return 1
    fi
    
    # Check if the test file exists
    if [ ! -f "tests/ui/test_functional_puppeteer.js" ]; then
        echo -e "${RED}Functional test file not found: tests/ui/test_functional_puppeteer.js${NC}"
        return 1
    fi
    
    # Run the Puppeteer tests
    node tests/ui/test_functional_puppeteer.js
    TEST_RESULT=$?
    
    if [ ${TEST_RESULT} -eq 0 ]; then
        echo -e "${GREEN}Functional tests passed successfully!${NC}"
    else
        echo -e "${RED}Functional tests failed with exit code ${TEST_RESULT}${NC}"
    fi
    
    return ${TEST_RESULT}
}

# Function to clean up after tests
cleanup_after_tests() {
    echo -e "\n${BOLD}${YELLOW}Cleaning up after tests...${NC}"
    
    # Kill all services
    pkill -f "gunicorn.*${BACKEND_PORT}"
    pkill -f "gunicorn.*${FRONTEND_PORT}"
    pkill -f "python.*${AI_PORT}"
    
    echo "All test processes terminated"
}

# Main execution
main() {
    # Clean up any existing processes
    cleanup_ports
    
    # Set up test environment
    setup_test_env
    
    # Run functional tests
    run_functional_tests
    TEST_RESULT=$?
    
    # Clean up after tests
    cleanup_after_tests
    
    # Exit with test result
    exit ${TEST_RESULT}
}

# Run main function
main
