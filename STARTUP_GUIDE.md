# Net-Swift Orchestrator - Startup Guide

## Architecture Overview

The application consists of three main components:

1. **Frontend Service** - Flask application serving the web UI (Port 5000)
2. **Backend Service** - Flask API providing device management and configuration (Port 5050)
3. **AI Microservice** - Mock AI service for configuration analysis (Port 5004)

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
curl http://127.0.0.1:5004/health
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

Verify it's running by accessing http://127.0.0.1:5000/login in your browser.

## Starting the Full Stack with One Command

For convenience, you can start all services in background mode with:

```sh
# Start all services in background
cd net-swift-orchestrator
nohup python backend_mock/mock_ai_service.py > ai_microservice.log 2>&1 &
cd backend && nohup python app.py > ../backend.log 2>&1 &
cd .. && nohup python -m frontend_py.app > frontend.log 2>&1 &

# Verify all services are running
curl http://127.0.0.1:5004/health
curl http://127.0.0.1:5050/api/health
curl -s http://127.0.0.1:5000/login | head -n 5
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
   lsof -i :5000
   lsof -i :5050
   lsof -i :5004
   ```

2. Kill existing processes if needed:
   ```sh
   kill -9 $(ps aux | grep -E 'mock_ai_service|app.py|frontend_py' | grep -v grep | awk '{print $2}')
   ```

3. Verify connectivity to services:
   ```sh
   # Check if ports are open
   nc -zv 127.0.0.1 5004 5050 5000
   
   # Check health endpoints with timeout
   curl -m 7 http://127.0.0.1:5004/health
   curl -m 7 http://127.0.0.1:5050/api/health
   curl -m 7 http://127.0.0.1:5000/login
   ```

4. Check service logs:
   ```sh
   tail -n 50 ai_microservice.log
   tail -n 50 backend.log
   tail -n 50 frontend.log
   ```

## Environment Variables

The application uses the following environment variables (defaults shown):

- `FRONTEND_URL=http://127.0.0.1:5000`
- `BACKEND_URL=http://127.0.0.1:5050`
- `AI_AGENT_URL=http://127.0.0.1:5004`

You can override these by setting them in your environment before starting the services.

## Service Endpoints

### Frontend Service (Port 5000)
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

### AI Microservice (Port 5004)
- `/health` - Health check endpoint
- `/api/rag_query` - RAG query endpoint
- `/api/analyze_config` - Configuration analysis endpoint
