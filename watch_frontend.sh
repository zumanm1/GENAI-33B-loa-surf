#!/bin/bash

# Script to watch for changes in frontend_py directory and restart the Flask server

FRONTEND_DIR="/Users/macbook/GENAI-33-LOVEAB/net-swift-orchestrator/frontend_py"
PORT=5051

echo "=== Flask Auto-Reloader for Frontend ==="
echo "Monitoring changes in $FRONTEND_DIR"
echo "Will restart Flask on port $PORT when changes are detected"

# Function to restart the Flask frontend service
restart_flask() {
    echo "$(date +"%Y-%m-%d %H:%M:%S") - Changes detected, restarting Flask frontend..."
    
    # Kill existing Flask service on port 5051
    PID=$(lsof -t -i:$PORT 2>/dev/null)
    if [ ! -z "$PID" ]; then
        echo "Stopping Flask service (PID: $PID)..."
        kill -9 $PID 2>/dev/null
    fi
    
    # Wait for port to be free
    while lsof -i:$PORT >/dev/null 2>&1; do
        echo "Waiting for port $PORT to be free..."
        sleep 1
    done
    
    # Start Flask in development mode with auto-reload enabled
    echo "Starting Flask frontend service..."
    cd "$FRONTEND_DIR" && FLASK_ENV=development FLASK_APP=app.py FLASK_DEBUG=1 python -m flask run --port $PORT --host 0.0.0.0 &
    
    echo "Flask restarted on port $PORT"
}

# Initial start
restart_flask

# Watch for changes in the frontend directory
while true; do
    # Using fswatch if available (more efficient)
    if command -v fswatch >/dev/null 2>&1; then
        echo "Using fswatch to monitor changes..."
        fswatch -o "$FRONTEND_DIR" | while read f; do
            echo "Change detected in: $f"
            restart_flask
        done
        break
    else
        # Fallback to simple polling with find and stat
        echo "fswatch not found, using polling method..."
        
        # Store current timestamp of the directory
        LAST_MODIFIED=$(find "$FRONTEND_DIR" -type f -name "*.py" -o -name "*.html" | xargs stat -f "%m" | sort -n -r | head -1)
        
        # Sleep for a bit
        sleep 2
        
        # Check if any files have been modified
        NEW_MODIFIED=$(find "$FRONTEND_DIR" -type f -name "*.py" -o -name "*.html" | xargs stat -f "%m" | sort -n -r | head -1)
        
        if [ "$NEW_MODIFIED" != "$LAST_MODIFIED" ]; then
            restart_flask
        fi
    fi
done
