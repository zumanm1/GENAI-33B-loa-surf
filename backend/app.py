
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import json
import pathlib

# Database file inside backend directory to stay consistent with start_services.sh cleanup
BASE_DIR = pathlib.Path(__file__).parent
DB_PATH = str(BASE_DIR / 'network_automation.db')
import logging
import json
import secrets
from datetime import datetime
import sqlite3
import bcrypt
from pathlib import Path
from backend.services.ai_agent_client import AIAgentClient
from baseline_core.routes import bp as baseline_bp

# Network automation imports (lazy-loaded inside functions to speed up startup)
ConnectHandler = None
InitNornir = None
napalm_get = None
get_network_driver = None
loader = None
load = None

# Helper to lazily import heavy libraries only when needed
def _lazy_import_network_libs():
    global ConnectHandler, InitNornir, napalm_get, get_network_driver, loader, load
    if ConnectHandler is None:
        try:
            from netmiko import ConnectHandler as _CH
            ConnectHandler = _CH
        except ImportError:
            pass
    if InitNornir is None:
        try:
            from nornir import InitNornir as _IN
            InitNornir = _IN
            from nornir_napalm.plugins.tasks import napalm_get as _NGET
            napalm_get = _NGET
            from nornir.core.task import Task, Result  # noqa: F401  # ensure side effect imports
        except ImportError:
            pass
    if get_network_driver is None:
        try:
            from napalm import get_network_driver as _GND
            get_network_driver = _GND
        except ImportError:
            pass
    if loader is None or load is None:
        try:
            from pyats.topology import loader as _loader
            from genie.testbed import load as _load
            loader = _loader
            load = _load
        except ImportError:
            pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize AI Agent Client
ai_agent = AIAgentClient()

app.register_blueprint(baseline_bp, url_prefix="/api")

# Device inventory for EVE-NG routers
DEVICE_INVENTORY = {
    'R15': {
        'host': '172.16.39.102',
        'port': 32783,
        'username': 'cisco',
        'password': 'cisco',
        'device_type': 'cisco_ios_telnet',
        'platform': 'ios'
    },
    'R16': {
        'host': '172.16.39.102',
        'port': 32773,
        'username': 'cisco',
        'password': 'cisco',
        'device_type': 'cisco_ios_telnet',
        'platform': 'ios'
    },
    'R17': {
        'host': '172.16.39.102',
        'port': None,  # To be provided
        'username': 'cisco',
        'password': 'cisco',
        'device_type': 'cisco_ios_telnet',
        'platform': 'ios'
    },
    'R18': {
        'host': '172.16.39.102',
        'port': None,  # To be provided
        'username': 'cisco',
        'password': 'cisco',
        'device_type': 'cisco_ios_telnet',
        'platform': 'ios'
    },
    'R19': {
        'host': '172.16.39.102',
        'port': None,  # To be provided
        'username': 'cisco',
        'password': 'cisco',
        'device_type': 'cisco_ios_telnet',
        'platform': 'ios'
    },
    'R20': {
        'host': '172.16.39.102',
        'port': None,  # To be provided
        'username': 'cisco',
        'password': 'cisco',
        'device_type': 'cisco_ios_telnet',
        'platform': 'ios'
    }
}

def init_database():
    """Initialize SQLite database for storing configurations and job history"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config_backups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device TEXT NOT NULL,
            command TEXT NOT NULL,
            output TEXT NOT NULL,
            method TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            parsed_data TEXT
        )
    ''')
    
    # Users table for authentication
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT UNIQUE NOT NULL,
            password BLOB NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device TEXT NOT NULL,
            job_type TEXT NOT NULL,
            status TEXT NOT NULL,
            details TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create default admin user if it doesn't exist
    cursor.execute('SELECT username FROM users WHERE username = ?', ('admin',))
    if not cursor.fetchone():
        import bcrypt
        # Hash password 'admin' with bcrypt
        hashed_password = bcrypt.hashpw('admin'.encode('utf-8'), bcrypt.gensalt())
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                       ('admin', hashed_password))
        print("Default admin user created with username 'admin' and password 'admin'")
    
    conn.commit()
    conn.close()

def save_config_backup(device, command, output, method, parsed_data=None):
    """Save configuration backup to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO config_backups (device, command, output, method, parsed_data)
        VALUES (?, ?, ?, ?, ?)
    ''', (device, command, output, method, json.dumps(parsed_data) if parsed_data else None))
    
    conn.commit()
    conn.close()

def retrieve_config_netmiko(device_name, command):
    _lazy_import_network_libs()
    """Retrieve configuration using Netmiko"""
    try:
        device_info = DEVICE_INVENTORY.get(device_name)
        if not device_info or not device_info.get('port'):
            return {'error': f'Device {device_name} not found or port not configured'}
        
        connection = ConnectHandler(**device_info)
        output = connection.send_command(command)
        connection.disconnect()
        
        return {'success': True, 'output': output, 'method': 'netmiko'}
        
    except Exception as e:
        logger.error(f"Netmiko error for {device_name}: {str(e)}")
        return {'error': str(e)}

def retrieve_config_napalm(device_name, command):
    _lazy_import_network_libs()
    """Retrieve configuration using NAPALM"""
    try:
        device_info = DEVICE_INVENTORY.get(device_name)
        if not device_info or not device_info.get('port'):
            return {'error': f'Device {device_name} not found or port not configured'}
        
        driver = get_network_driver('ios')
        device = driver(
            hostname=device_info['host'],
            username=device_info['username'],
            password=device_info['password'],
            optional_args={'port': device_info['port']}
        )
        
        device.open()
        
        # NAPALM has specific getters, map commands to getters
        if 'interface' in command.lower():
            result = device.get_interfaces()
        elif 'version' in command.lower():
            result = device.get_facts()
        else:
            # For other commands, use CLI
            result = device.cli([command])
            
        device.close()
        
        return {'success': True, 'output': result, 'method': 'napalm'}
        
    except Exception as e:
        logger.error(f"NAPALM error for {device_name}: {str(e)}")
        return {'error': str(e)}

def retrieve_config_pyats(device_name, command):
    _lazy_import_network_libs()
    """Retrieve and parse configuration using PyATS/Genie"""
    try:
        device_info = DEVICE_INVENTORY.get(device_name)
        if not device_info or not device_info.get('port'):
            return {'error': f'Device {device_name} not found or port not configured'}
        
        # Create testbed for PyATS
        testbed_dict = {
            'devices': {
                device_name: {
                    'connections': {
                        'cli': {
                            'protocol': 'telnet',
                            'ip': device_info['host'],
                            'port': device_info['port']
                        }
                    },
                    'credentials': {
                        'default': {
                            'username': device_info['username'],
                            'password': device_info['password']
                        }
                    },
                    'os': 'iosxe',
                    'type': 'router'
                }
            }
        }
        
        testbed = load(testbed_dict)
        device = testbed.devices[device_name]
        device.connect()
        
        # Execute command and parse with Genie
        if 'ip int brief' in command.lower():
            parsed_output = device.parse('show ip interface brief')
        elif 'version' in command.lower():
            parsed_output = device.parse('show version')
        else:
            # For other commands, execute raw and try to parse
            raw_output = device.execute(command)
            try:
                parsed_output = device.parse(command)
            except:
                parsed_output = {'raw_output': raw_output}
        
        device.disconnect()
        
        return {
            'success': True, 
            'output': parsed_output, 
            'method': 'pyats_genie',
            'parsed': True
        }
        
    except Exception as e:
        logger.error(f"PyATS/Genie error for {device_name}: {str(e)}")
        return {'error': str(e)}

@app.route('/')
def index():
    """Serve the main application page"""
    return jsonify({
        'message': 'Network Automation Platform API',
        'version': '1.0',
        'endpoints': {
            'config_retrieve': '/api/config/retrieve',
            'config_push': '/api/config/push',
            'devices': '/api/devices',
            'health': '/api/health'
        }
    })

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'available_devices': list(DEVICE_INVENTORY.keys())
    })

@app.route('/api/devices')
def get_devices():
    """Get list of available devices"""
    devices = []
    for name, info in DEVICE_INVENTORY.items():
        devices.append({
            'name': name,
            'host': info['host'],
            'port': info['port'],
            'available': info['port'] is not None
        })
    return jsonify({'devices': devices})

@app.route('/api/config/retrieve', methods=['POST'])
def config_retrieve():
    """Configuration retrieve endpoint - supports multiple automation methods"""
    try:
        data = request.get_json()
        
        # Validate input
        device = data.get('device')
        command = data.get('command', 'show ip interface brief')
        method = data.get('method', 'netmiko')
        save_backup = data.get('save_backup', True)
        
        if not device:
            return jsonify({'error': 'Device name is required'}), 400
        
        if device not in DEVICE_INVENTORY:
            return jsonify({'error': f'Device {device} not found in inventory'}), 404
        
        # Execute based on selected method
        if method == 'netmiko':
            result = retrieve_config_netmiko(device, command)
        elif method == 'napalm':
            result = retrieve_config_napalm(device, command)
        elif method == 'pyats' or method == 'genie':
            result = retrieve_config_pyats(device, command)
        else:
            return jsonify({'error': f'Unsupported method: {method}'}), 400
        
        if 'error' in result:
            return jsonify(result), 500
        
        # Save backup if requested
        if save_backup and 'output' in result:
            parsed_data = result.get('output') if result.get('parsed') else None
            output_str = json.dumps(result['output']) if isinstance(result['output'], dict) else str(result['output'])
            save_config_backup(device, command, output_str, method, parsed_data)
        
        return jsonify({
            'success': True,
            'device': device,
            'command': command,
            'method': result['method'],
            'output': result['output'],
            'parsed': result.get('parsed', False),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Config retrieve error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/config/push', methods=['POST'])
def config_push():
    """Configuration push endpoint - placeholder for future implementation"""
    try:
        data = request.get_json()
        
        device = data.get('device')
        commands = data.get('commands', [])
        method = data.get('method', 'netmiko')
        
        if not device or not commands:
            return jsonify({'error': 'Device and commands are required'}), 400
        
        # For now, return a placeholder response
        return jsonify({
            'success': True,
            'message': 'Config push endpoint - implementation coming soon',
            'device': device,
            'commands': commands,
            'method': method,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Config push error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/test/connectivity', methods=['POST'])
def test_connectivity():
    """Test connectivity to devices"""
    try:
        data = request.get_json()
        devices_to_test = data.get('devices', list(DEVICE_INVENTORY.keys()))
        
        results = {}
        for device_name in devices_to_test:
            if device_name in DEVICE_INVENTORY:
                device_info = DEVICE_INVENTORY[device_name]
                if device_info.get('port'):
                    try:
                        connection = ConnectHandler(**device_info)
                        connection.disconnect()
                        results[device_name] = {'status': 'online', 'error': None}
                    except Exception as e:
                        results[device_name] = {'status': 'offline', 'error': str(e)}
                else:
                    results[device_name] = {'status': 'unconfigured', 'error': 'Port not configured'}
            else:
                results[device_name] = {'status': 'unknown', 'error': 'Device not in inventory'}
        
        return jsonify({'results': results})
        
    except Exception as e:
        logger.error(f"Connectivity test error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

# -----------------------------
# User Authentication
# -----------------------------

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json(silent=True) or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'username and password required'}), 400
    try:
        conn = sqlite3.connect(DB_PATH)

        c = conn.cursor()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        c.execute('INSERT INTO users(username, password) VALUES(?, ?)', (username, hashed_password))
        conn.commit()
        conn.close()
        return jsonify({'message': 'registered', 'username': username}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'user already exists'}), 409

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'username and password required'}), 400
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT password FROM users WHERE username = ?', (username,))
    row = c.fetchone()
    conn.close()
    if row:
        # Handle password hash that might be stored as string or bytes
        hashed_password = row[0]
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')
        try:
            if bcrypt.checkpw(password.encode('utf-8'), hashed_password):
                token = secrets.token_hex(16)
                return jsonify({'username': username, 'auth_token': token})
        except ValueError:
            # Malformed hash in DB (shouldn't happen); treat as invalid credentials
            pass
    return jsonify({'error': 'invalid credentials'}), 401

# AI Agent health check endpoint
@app.route('/api/ai/health', methods=['GET'])
def ai_agent_health():
    """Proxy for the AI Agent's health check."""
    health_status = ai_agent.check_health()
    status_code = 200 if health_status.get('status') != 'unreachable' else 503
    return jsonify(health_status), status_code

@app.route('/api/ai/rag_query', methods=['POST'])
def ai_rag_query():
    """Expose the AI Agent's RAG query functionality."""
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({'error': 'Query is required'}), 400
    
    result = ai_agent.query_rag(data['query'])
    return jsonify(result)

@app.route('/api/ai/analyze_config', methods=['POST'])
def ai_analyze_config():
    """Expose the AI Agent's configuration analysis functionality."""
    data = request.get_json()
    if not data or 'config_text' not in data:
        return jsonify({'error': 'Configuration text is required'}), 400

    result = ai_agent.analyze_config(data['config_text'], data.get('device_name'))
    return jsonify(result)

@app.route('/api/ai/config', methods=['GET'])
def get_ai_config():
    """Retrieve the current AI configuration."""
    try:
        with open('backend/config.json', 'r') as f:
            config = json.load(f)
        return jsonify(config)
    except FileNotFoundError:
        return jsonify({'error': 'AI configuration file not found.'}), 404
    except Exception as e:
        logger.error(f"Error reading AI config: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/config', methods=['POST'])
def update_ai_config():
    """Update the AI configuration."""
    try:
        new_config = request.get_json()
        # Optionally, add validation for the new_config structure here
        with open('backend/config.json', 'w') as f:
            json.dump(new_config, f, indent=4)
        # Here you might want to signal the AI service to reload the config
        return jsonify({'message': 'AI configuration updated successfully.'})
    except Exception as e:
        logger.error(f"Error updating AI config: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Retrieve the latest RAG processor logs."""
    log_file_path = 'logs/rag_processor.log'
    try:
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r') as f:
                # Read last 100 lines to avoid sending huge files
                lines = f.readlines()
                log_content = "".join(lines[-100:])
            return jsonify({'logs': log_content})
        else:
            return jsonify({'logs': 'Log file not found. Waiting for RAG processor to generate logs...\n'})
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/events', methods=['GET'])
def get_events():
    """Retrieve recent system events for the dashboard"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # First check if the events table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
        if not cursor.fetchone():
            # Create events table if it doesn't exist
            cursor.execute("""
                CREATE TABLE events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    device_name TEXT,
                    event_type TEXT,
                    description TEXT
                )
            """)
            conn.commit()
            
            # Add some sample events data
            current_time = datetime.now().isoformat()
            sample_events = [
                (current_time, 'R15', 'CONFIG_BACKUP', 'Configuration backup successful'),
                (current_time, 'R16', 'CONNECTIVITY', 'Device connectivity restored'),
                (current_time, 'System', 'STARTUP', 'Net-Swift Orchestrator services started')
            ]
            cursor.executemany(
                "INSERT INTO events (timestamp, device_name, event_type, description) VALUES (?, ?, ?, ?)",
                sample_events
            )
            conn.commit()
        
        # Get events sorted by timestamp
        cursor.execute("""
            SELECT id, timestamp, device_name, event_type, description 
            FROM events 
            ORDER BY timestamp DESC 
            LIMIT 20
        """)
        events = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(events)
    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/backups', methods=['GET'])
def get_backups():
    """Retrieve all configuration backups from the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, device, command, method, timestamp, parsed_data IS NOT NULL as has_parsed_data FROM config_backups ORDER BY timestamp DESC")
        backups = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(backups)
    except Exception as e:
        logger.error(f"Error fetching backups: {e}")
        return jsonify({"error": str(e)}), 500

# Ensure database is ready when running under gunicorn / any WSGI server
init_database()

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # Create directories
    os.makedirs('backups', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    print("🚀 Starting Network Automation Platform...")
    print("📡 Management IP: 172.16.39.102")
    print("🖥️  Available devices: R15 (port 32783), R16 (port 32773)")
    print("⚠️  R17-R20 ports need to be configured")
    print("🌐 Web interface: http://localhost:5051")
    print("🔌 API base: http://localhost:5051/api")
    
    app.run(debug=True, host='0.0.0.0', port=5050)
