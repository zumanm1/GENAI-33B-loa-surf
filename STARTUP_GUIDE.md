# Net-Swift Orchestrator - Startup Guide

This guide provides the necessary steps to launch the complete Net-Swift Orchestrator application stack.

## Prerequisites

Ensure you have all the necessary Python packages installed from `requirements.txt`. Additionally, this setup now uses `gunicorn` as the WSGI server for the backend and frontend services for improved performance and stability.

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Install Gunicorn:**
    ```bash
    pip install gunicorn
    ```

## Service Startup Sequence

It is recommended to start the services in the following order. All commands should be run from the project's root directory (`net-swift-orchestrator`).

### 1. AI Agent Service

*   **Port:** `5052`
*   **Command:**
    ```bash
    nohup python3 ai_agent_py/main.py > ai_agent.log 2>&1 &
    ```

### 2. Backend Service

*   **Port:** `5050`
*   **Command:**
    ```bash
    cd backend
    nohup gunicorn --bind 0.0.0.0:5050 --workers 4 'app:app' > ../backend.log 2>&1 &
    cd ..
    ```

### 3. Frontend Service

*   **Port:** `5051`
*   **Command:**
    ```bash
    cd frontend_py
    nohup gunicorn --bind 0.0.0.0:5051 --workers 4 'app:app' > ../frontend.log 2>&1 &
    cd ..
    ```

## Verifying the Setup

After launching all services, you can check their respective log files (`ai_agent.log`, `backend.log`, `frontend.log`) for any errors. The application should be accessible at `http://127.0.0.1:5051`.


## Architecture Overview

The application consists of three main components:

1. **Frontend Service** - Flask application serving the web UI (Port 5051)
2. **Backend Service** - Flask API providing device management and configuration (Port 5050)
3. **AI Microservice** - Mock AI service for configuration analysis (Port 5052)

## Prerequisites

- Python 3.8+
- pip
- Node.js 14+ (for Puppeteer tests)
- Browser for UI testing (Chrome/Firefox)

## Installation

1. Clone the repository:
   ```sh
   git clone <repository-url>
   cd net-swift-orchestrator
   ```

2. Set up Python virtual environments (recommended):
   ```sh
   # For backend
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   pip install -r requirements.txt
   cd ..

   # For frontend
   cd frontend_py
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   pip install -r requirements.txt
   cd ..
   ```

3. Install Node.js dependencies for UI testing:
   ```sh
   cd tests/ui
   npm install
   cd ../..
   ```

4. Install Playwright dependencies:
   ```sh
   pip install pytest-playwright
   playwright install
   ```

## Starting the Application Stack

For proper operation, the services must be started in the following order:

### 1. Start the AI Microservice

```sh
cd net-swift-orchestrator
python backend_mock/mock_ai_service.py
```

Verify it's running:
```sh
curl http://127.0.0.1:5052/health
# Should return: {"status":"ok"}
```

### 2. Start the Backend Service

In a new terminal:
```sh
cd net-swift-orchestrator/backend
python app.py
```

Verify it's running:
```sh
curl http://127.0.0.1:5050/api/health
# Should return JSON with status: "healthy" and available devices
```

### 3. Start the Frontend Service

In a new terminal:
```sh
cd net-swift-orchestrator
python -m frontend_py.app
```

Verify it's running by accessing http://127.0.0.1:5051/login in your browser.

## Starting the Full Stack with One Command

For convenience, you can start all services in background mode with:

```sh
# Start all services in background
cd net-swift-orchestrator
nohup python backend_mock/mock_ai_service.py > ai_microservice.log 2>&1 &
cd backend && nohup python app.py > ../backend.log 2>&1 &
cd .. && nohup python -m frontend_py.app > frontend.log 2>&1 &

# Verify all services are running
curl http://127.0.0.1:5052/health
curl http://127.0.0.1:5050/api/health
curl -s http://127.0.0.1:5051/login | head -n 5
```

## Stopping the Application Stack

To stop all running services:

```sh
kill -9 $(ps aux | grep -E 'mock_ai_service|app.py|frontend_py' | grep -v grep | awk '{print $2}')
```

## Running UI Tests

### Playwright Tests (Python)

```sh
cd net-swift-orchestrator
pytest tests/ui/test_login_playwright.py -v
```

### Puppeteer Tests (JavaScript)

```sh
cd net-swift-orchestrator/tests/ui
node test_login_puppeteer.js
```

## Troubleshooting

If you encounter issues starting the services:

1. Check if ports are already in use:
   ```sh
   lsof -i :5051
   lsof -i :5050
   lsof -i :5052
   ```

2. Kill existing processes if needed:
   ```sh
   kill -9 $(ps aux | grep -E 'mock_ai_service|app.py|frontend_py' | grep -v grep | awk '{print $2}')
   ```

3. Verify connectivity to services:
   ```sh
   # Check if ports are open
   nc -zv 127.0.0.1 5052 5050 5051
   
   # Check health endpoints with timeout
   curl -m 7 http://127.0.0.1:5052/health
   curl -m 7 http://127.0.0.1:5050/api/health
   curl -m 7 http://127.0.0.1:5051/login
   ```

4. Check service logs:
   ```sh
   tail -n 50 ai_microservice.log
   tail -n 50 backend.log
   tail -n 50 frontend.log
   ```

## Environment Variables

The application uses the following environment variables (defaults shown):

- `FRONTEND_URL=http://127.0.0.1:5051`
- `BACKEND_URL=http://127.0.0.1:5050`
- `AI_AGENT_URL=http://127.0.0.1:5052`

You can override these by setting them in your environment before starting the services.

## Service Endpoints

### Frontend Service (Port 5051)
- `/login` - Login page
- `/register` - Registration page
- `/` - Dashboard (requires authentication)
- `/devices` - Device management (requires authentication)
- `/config/<device_name>` - Device configuration (requires authentication)

### Backend Service (Port 5050)
- `/api/health` - Health check endpoint
- `/api/devices` - List available devices
- `/api/login` - Authentication endpoint
- `/api/register` - User registration
- `/api/config/retrieve` - Retrieve device configuration
- `/api/config/push` - Push configuration to device
- `/api/connectivity/test` - Test device connectivity
- `/api/backups` - List configuration backups

### AI Microservice (Port 5052)
- `/health` - Health check endpoint
- `/api/rag_query` - RAG query endpoint
- `/api/analyze_config` - Configuration analysis endpoint
