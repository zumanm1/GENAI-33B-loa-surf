#!/bin/bash

# This script starts all the services for the Net-Swift Orchestrator application.
# It should be run from the project root directory.

echo "Starting all services..."

# Kill any existing processes bound to the service ports to avoid conflicts
echo "Ensuring ports 5050, 5051, 5052 are free..."
# Use lsof to find any PIDs listening on our service ports and terminate them (order: 5051, 5050, 5052)
for PORT in 5051 5050 5052; do
  PIDS=$(lsof -ti :$PORT 2>/dev/null)
  if [[ -n "$PIDS" ]]; then
    echo "Killing processes on port $PORT: $PIDS"
    kill -9 $PIDS || true
  fi
done

# Ensure we are in the script's directory
cd "$(dirname "$0")"

# Clean up old database to ensure a fresh start and correct schema
echo "Removing old database to ensure correct schema..."
rm -f backend/network_automation.db

# Start Backend Service
echo "Starting Backend on http://127.0.0.1:5050"
export FLASK_APP=backend/app.py
gunicorn --bind 0.0.0.0:5050 --workers 1 --threads 8 backend.app:app & 
BACKEND_PID=$!

# Start Frontend Service
echo "Starting Frontend on http://127.0.0.1:5051"
DISABLE_AUTO_LOGIN=true gunicorn --bind 0.0.0.0:5051 --workers 1 --log-level info --log-file frontend.log frontend_py.app:app &
FRONTEND_PID=$!

# Start AI Service
echo "Starting AI Service on http://127.0.0.1:5052"
(cd ai_service && gunicorn --bind 0.0.0.0:5052 --workers 1 --log-level info --log-file ../ai_microservice.log app:app) &
AI_PID=$!

echo ""
# Optional: quick health-check loop (max 30s)
echo "Waiting for services to respond..."
for i in {1..30}; do
  BACK=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5050/ || true)
  FRONT=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5051/ || true)
  AI=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5052/ || true)
  if [[ "$BACK" != "000" && "$FRONT" != "000" && "$AI" != "000" ]]; then
     echo "All services are up: backend=$BACK frontend=$FRONT ai=$AI"; break
  fi
  sleep 1
  if [[ $i -eq 30 ]]; then echo "Warning: services did not all become ready in time."; fi
done

echo "Services started with the following PIDs:"
echo "- Backend: $BACKEND_PID"
echo "- Frontend: $FRONTEND_PID"
echo "- AI Service: $AI_PID"
echo ""

# Provide a command to stop the services
echo "To stop all services, run the following command:"
echo "kill $BACKEND_PID $FRONTEND_PID $AI_PID"
