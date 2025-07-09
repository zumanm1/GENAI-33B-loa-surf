#!/bin/bash
#
# This script waits for all required services to be healthy before proceeding.
#
echo '--- Waiting for services with curl ---'

# Define service URLs
AI_URL="http://127.0.0.1:5004/health"
BACKEND_URL="http://127.0.0.1:5050/api/health"
FRONTEND_URL="http://127.0.0.1:5051/login"

# Set a 30-second timeout
END_TIME=$(( $(date +%s) + 30 ))

while true; do
  # Use curl to check the HTTP status code of each service
  ai_status=$(curl --connect-timeout 5 -s -o /dev/null -w "%{http_code}" "$AI_URL")
  backend_status=$(curl --connect-timeout 5 -s -o /dev/null -w "%{http_code}" "$BACKEND_URL")
  frontend_status=$(curl --connect-timeout 5 -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL")

  echo "AI Service: $ai_status, Backend: $backend_status, Frontend: $frontend_status"

  # Check if all services returned a 200 status code
  if [ "$ai_status" -eq 200 ] && [ "$backend_status" -eq 200 ] && [ "$frontend_status" -eq 200 ]; then
    echo '--- All services are UP. ---'
    exit 0
  fi

  # Check if the timeout has been reached
  if [ $(date +%s) -gt $END_TIME ]; then
    echo '--- Services did not start in time. Aborting. ---'
    exit 1
  fi

  # Wait before retrying
  sleep 2
done
