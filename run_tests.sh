#!/bin/bash

# Clean up old database file to ensure fresh schema
rm -f ./backend/network_automation.db

# Exit immediately if a command exits with a non-zero status.
set -e

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to the script's directory to ensure relative paths work
cd "$SCRIPT_DIR"

echo "Installing Python dependencies..."
pip install -r requirements.txt

# --- Cleanup Function ---
cleanup() {
    echo "Cleaning up background processes..."
    # Kill all processes in the group of this script
    if [ -n "$BACKEND_PID" ]; then kill $BACKEND_PID; fi
    if [ -n "$FRONTEND_PID" ]; then kill $FRONTEND_PID; fi
    if [ -n "$AI_PID" ]; then kill $AI_PID; fi
}

# Trap EXIT signal to ensure cleanup runs on script exit
trap cleanup EXIT

# --- Start Services ---
echo "Starting backend and frontend services..."

# Disable auto-login for tests to ensure a clean state
export DISABLE_AUTO_LOGIN=true

# Clean up old database to ensure a fresh schema
rm -f backend/network_automation.db

# Start Backend
export FLASK_APP=backend/app.py
# Run gunicorn from the root so that baseline_core is on the python path
gunicorn --bind 0.0.0.0:5050 backend.app:app &
BACKEND_PID=$!

# Start Frontend
cd frontend_py
gunicorn --bind 0.0.0.0:5051 app:app & 
FRONTEND_PID=$!
cd ..

# Start AI Service
cd ai_service
gunicorn --bind 0.0.0.0:5052 app:app & 
AI_PID=$!
cd ..

echo "Backend PID: $BACKEND_PID, Frontend PID: $FRONTEND_PID, AI PID: $AI_PID"

# --- Health Check ---
echo "Waiting for services to become available..."

# Wait for frontend (port 5051)
while ! nc -z 127.0.0.1 5051; do   
  sleep 0.5 # wait for 0.5 second before check again
done
echo "Frontend service is up."

# Wait for backend (port 5050)
while ! nc -z 127.0.0.1 5050; do   
  sleep 0.5 # wait for 0.5 second before check again
done
echo "Backend service is up."

# Wait for AI service (port 5052)
while ! nc -z 127.0.0.1 5052; do
  sleep 0.5 # wait for 0.5 second before check again
done
echo "AI service is up."

echo "Services are ready. Running tests..."

# --- Run Tests ---
# Note: This assumes Ollama (llama2 model) is already running separately
npm test

# --- Exit ---
# The cleanup function will be called automatically on exit
echo "Tests finished."
