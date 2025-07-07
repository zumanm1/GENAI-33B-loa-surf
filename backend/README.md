
# Network Automation Platform - Backend

A comprehensive Flask-based backend for network automation using multiple libraries (Netmiko, NAPALM, Nornir, PyATS/Genie) to manage Cisco routers in EVE-NG environments.

## Features

- **Multiple Automation Libraries**: Netmiko, NAPALM, Nornir, PyATS/Genie support
- **Configuration Retrieve**: Execute commands and get both raw and parsed output
- **Configuration Push**: Deploy configurations (placeholder for future implementation)
- **Database Storage**: SQLite database for configuration backups and job history
- **RESTful API**: Complete API for integration with frontend applications
- **Device Management**: Support for multiple Cisco routers via telnet console

## Quick Start

### 1. Setup
```bash
# Make setup script executable
chmod +x setup.sh

# Run setup (creates venv, installs packages, tests connectivity)
./setup.sh

# Activate virtual environment
source venv/bin/activate
```

### 2. Configure Device Ports
Edit `app.py` and update the missing router ports:
```python
DEVICE_INVENTORY = {
    'R17': {'port': YOUR_R17_PORT},  # Update with actual port
    'R18': {'port': YOUR_R18_PORT},  # Update with actual port
    'R19': {'port': YOUR_R19_PORT},  # Update with actual port
    'R20': {'port': YOUR_R20_PORT}   # Update with actual port
}
```

### 3. Start Application
```bash
python app.py
```

### 4. Test API
```bash
python test_api.py
```

## API Endpoints

### Health & Status
- `GET /api/health` - Health check and system status
- `GET /api/devices` - List available devices

### Configuration Management  
- `POST /api/config/retrieve` - Retrieve configurations
- `POST /api/config/push` - Push configurations (placeholder)

### Testing
- `POST /api/test/connectivity` - Test device connectivity

## Configuration Retrieve Examples

### Using Netmiko
```bash
curl -X POST http://localhost:5000/api/config/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "device": "R15",
    "command": "show ip interface brief",
    "method": "netmiko",
    "save_backup": true
  }'
```

### Using PyATS/Genie (Parsed Output)
```bash
curl -X POST http://localhost:5000/api/config/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "device": "R15", 
    "command": "show version",
    "method": "pyats",
    "save_backup": true
  }'
```

### Using NAPALM
```bash
curl -X POST http://localhost:5000/api/config/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "device": "R15",
    "command": "show ip interface brief", 
    "method": "napalm",
    "save_backup": true
  }'
```

## Supported Commands

- `show ip interface brief` - Interface status and IP addresses
- `show version` - Device version and system information
- `show running-config` - Running configuration
- `show ip route` - Routing table
- Custom commands supported

## Device Configuration

### EVE-NG Setup
- **Management IP**: 172.16.39.102
- **Protocol**: Telnet console access
- **Credentials**: cisco/cisco

### Router Inventory
| Router | Console Port | Status |
|--------|-------------|---------|
| R15    | 32783       | ✅ Configured |
| R16    | 32773       | ✅ Configured |
| R17    | TBD         | ⚠️ Port needed |
| R18    | TBD         | ⚠️ Port needed |
| R19    | TBD         | ⚠️ Port needed |
| R20    | TBD         | ⚠️ Port needed |

## Database Schema

### config_backups table
- `id` - Primary key
- `device` - Device name
- `command` - Executed command
- `output` - Command output
- `method` - Automation method used
- `timestamp` - Execution time
- `parsed_data` - JSON parsed data (if available)

### jobs table
- `id` - Primary key  
- `device` - Target device
- `job_type` - Type of operation
- `status` - Job status
- `details` - Additional information
- `timestamp` - Job creation time

## Troubleshooting

### Common Issues

1. **EVE-NG Not Reachable**
   ```bash
   ping 172.16.39.102
   ```

2. **Telnet Connection Failed**
   ```bash
   telnet 172.16.39.102 32783  # Test R15
   telnet 172.16.39.102 32773  # Test R16
   ```

3. **Import Errors**
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Database Issues**
   - Check file permissions
   - Ensure sufficient disk space
   - Delete `network_automation.db` to recreate

### Testing Individual Components

```python
# Test Netmiko connection
from netmiko import ConnectHandler
device = {
    'host': '172.16.39.102',
    'port': 32783,
    'username': 'cisco', 
    'password': 'cisco',
    'device_type': 'cisco_ios_telnet'
}
connection = ConnectHandler(**device)
output = connection.send_command('show ip int brief')
print(output)
connection.disconnect()
```

## Next Steps

1. **Update Router Ports**: Get console ports for R17-R20 from EVE-NG
2. **Test Connectivity**: Verify all routers are accessible
3. **Implement Config Push**: Add commands to push configurations
4. **Add Authentication**: Implement API key or session-based auth
5. **Add Scheduling**: Support for scheduled configuration tasks

## Integration with Frontend

This backend is designed to work with the React frontend. Key integration points:

- **CORS Enabled**: Allows frontend API calls
- **JSON API**: All endpoints return JSON responses
- **Error Handling**: Consistent error response format
- **Status Codes**: Standard HTTP status codes for proper frontend handling

Start the backend server and point your frontend to `http://localhost:5000/api` for all API calls.
