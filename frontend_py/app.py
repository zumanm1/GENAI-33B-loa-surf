from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import requests
import functools
import secrets

app = Flask(__name__, template_folder='templates')
app.secret_key = secrets.token_hex(16)

# Configuration for the backend API
BACKEND_API_URL = "http://127.0.0.1:5050"

# Helper function for making authenticated API requests
def api_request(method, endpoint, **kwargs):
    """Make an authenticated request to the backend API."""
    url = f"{BACKEND_API_URL}{endpoint}"
    
    # Add auth token to headers if available
    headers = kwargs.get('headers', {})
    if 'auth_token' in session:
        headers['Authorization'] = f"Bearer {session['auth_token']}"
    kwargs['headers'] = headers
    
    # Include all backend session cookies in the request if available
    cookies = {}
    for key, value in session.items():
        if key.startswith('backend_'):
            # Extract the original cookie name by removing the 'backend_' prefix
            original_cookie_name = key[8:]
            cookies[original_cookie_name] = value
    
    # Merge with any cookies provided in kwargs
    if 'cookies' in kwargs:
        cookies.update(kwargs.pop('cookies'))
    
    # Add debug logging
    print(f"API Request to {url} with headers: {headers}")
    print(f"API Request cookies: {cookies}")
    
    # Make the request
    response = requests.request(method, url, cookies=cookies, **kwargs)
    
    # Debug response
    print(f"API Response status: {response.status_code}")
    if response.status_code != 200:
        print(f"API Response error: {response.text}")
        
    return response

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def login_required(view):
    """View decorator that redirects anonymous users to the login page."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

@app.context_processor
def inject_user():
    """Inject user session data into all templates."""
    return dict(username=session.get('username'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        try:
            # Create a session to maintain cookies
            s = requests.Session()
            response = s.post(f"{BACKEND_API_URL}/api/login", json={'username': username, 'password': password})
            
            if response.status_code == 200:
                session.clear()
                session['username'] = response.json().get('username')
                
                # Store auth token if provided
                if 'auth_token' in response.json():
                    session['auth_token'] = response.json().get('auth_token')
                    print(f"Stored auth token: {session['auth_token'][:10]}...")
                else:
                    # Generate a simple token from username as fallback
                    import hashlib
                    import time
                    token = hashlib.sha256(f"{username}:{time.time()}".encode()).hexdigest()
                    session['auth_token'] = token
                    print(f"Generated fallback auth token: {token[:10]}...")
                
                # Store all backend cookies for API requests
                for cookie_name, cookie_value in s.cookies.items():
                    session[f'backend_{cookie_name}'] = cookie_value
                    print(f"Storing backend cookie: {cookie_name} = {cookie_value}")
                
                # Debug: Print all session data
                print(f"Session after login: {session}")
                
                # Add success message
                flash(f'Welcome back, {username}! You have successfully logged in.', 'success')
                
                return redirect(url_for('index'))
            else:
                flash(response.json().get('error', 'Login failed.'), 'danger')
        except requests.exceptions.RequestException as e:
            flash(f"Error connecting to backend: {e}", 'danger')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        try:
            response = requests.post(f"{BACKEND_API_URL}/api/register", json={'username': username, 'password': password})
            if response.status_code in (201, 409):
                flash('registered successfully', 'success')
                return redirect(url_for('login'))
            else:
                flash(response.json().get('error', 'Registration failed.'), 'danger')
        except requests.exceptions.RequestException as e:
            flash(f"Error connecting to backend: {e}", 'danger')
    return render_template('register.html')


@app.route('/logout')
def logout():
    """Log the user out."""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    """Serve the dashboard page with live stats."""
    total_devices = online_devices = backups_count = 0
    devices = []
    backups = []
    events = []
    error = None
    error_backups = None
    error_events = None

    try:
        dev_resp = api_request('GET', '/api/devices', timeout=3)
        dev_resp.raise_for_status()
        devices = dev_resp.json()
        if isinstance(devices, dict) and 'devices' in devices:
            devices = devices['devices']
        total_devices = len(devices)
        online_devices = sum(1 for d in devices if d.get('status') == 'online')
    except requests.exceptions.RequestException as e:
        error = f"Error fetching devices: {e}"
        devices = []

    # Fetch backups for count
    try:
        response = api_request('GET', '/api/backups')
        response.raise_for_status()
        backups = response.json()
    except requests.exceptions.RequestException as e:
        error_backups = f"Error fetching backups: {e}"
        backups = []

    # Fetch latest events
    try:
        response = api_request('GET', '/api/events')
        response.raise_for_status()
        events = response.json()
    except requests.exceptions.RequestException as e:
        error_events = f"Error fetching events: {e}"
        events = []

    online_devices = [d for d in devices if d.get("status") == "online"]

    return render_template(
        "index.html",
        devices=devices,
        online_devices=len(online_devices),
        total_devices=len(devices),
        total_backups=len(backups),
        events=events,
        error=error,
        error_backups=error_backups,
        error_events=error_events,
    )

@app.route('/retrieve', methods=['GET', 'POST'])
@login_required
def retrieve():
    """Serve the config retrieve page and handle form submission"""
    devices_list = []
    error = None
    result = None

    try:
        response = api_request('GET', '/api/devices')
        response.raise_for_status()
        devices_list = response.json()
    except requests.exceptions.RequestException as e:
        error = f"Error fetching devices: {e}"

    if request.method == 'POST':
        device_name = request.form.get('device')
        command = request.form.get('command')
        if command == 'custom':
            command = request.form.get('custom_command')
        
        method = request.form.get('method')
        mode = 'live' if request.form.get('mode') == 'live' else 'mock'
        
        if not device_name or not command:
            error = "Device and command must be specified."
        else:
            try:
                api_response = api_request(
                    'POST',
                    '/api/config/retrieve',
                    json={"device_name": device_name, "command": command}
                )
                api_response.raise_for_status()
                result = api_response.json()
            except requests.exceptions.RequestException as e:
                if e.response:
                    try:
                        error = f"API Error: {e.response.json().get('error', e.response.text)}"
                    except requests.exceptions.JSONDecodeError:
                        error = f"API Error: {e.response.status_code} - {e.response.text}"
                else:
                    error = f"Error retrieving configuration: {e}"

    form_data = {
        'device': device_name,
        'command': command,
        'method': method,
        'mode': mode
    } if request.method == 'POST' and not error else None

    return render_template(
        "retrieve.html", 
        active_tab='retrieve', 
        devices=devices_list, 
        error=error, 
        result=result,
        form_data=form_data
    )

@app.route('/push', methods=['GET', 'POST'])
@login_required
def push():
    """Serve the config push page and handle form submission"""
    devices_list = []
    error = None
    result = None

    try:
        response = api_request('GET', '/api/devices')
        response.raise_for_status()
        devices_list = response.json()
    except requests.exceptions.RequestException as e:
        error = f"Error fetching devices: {e}"

    restore_data = None
    if request.method == 'GET':
        device_from_url = request.args.get('device')
        commands_from_url = request.args.get('commands')
        if device_from_url and commands_from_url:
            restore_data = {
                'device': device_from_url,
                'commands': commands_from_url
            }

    if request.method == 'POST':
        device_name = request.form.get('device')
        config_commands = request.form.get('config_commands').splitlines()
        mode = 'live' if request.form.get('mode') == 'live' else 'mock'

        try:
            api_response = api_request('POST', '/api/config/push', json={'device': device_name, 'commands': config_commands, 'mode': mode})
            api_response.raise_for_status()
            result = api_response.json()
        except requests.exceptions.RequestException as e:
            error = f"Error pushing configuration: {e}"

    return render_template("push.html", active_tab='push', devices=devices_list, error=error, result=result, restore_data=restore_data)

@app.route('/backups')
@login_required
def backups():
    """Serve the backups page and display backup history"""
    backups_list = []
    error = None
    try:
        response = api_request('GET', '/api/backups')
        response.raise_for_status()
        backups_list = response.json()
    except requests.exceptions.RequestException as e:
        error = f"Error fetching backups: {e}"
    
    return render_template("backups.html", active_tab='backups', backups=backups_list, error=error)

@app.route('/backup/<backup_id>')
@login_required
def backup_detail(backup_id):
    """Serve the backup detail page"""
    backup = None
    error = None
    try:
        response = api_request('GET', f'/api/backup/{backup_id}')
        response.raise_for_status()
        backup = response.json()
    except requests.exceptions.RequestException as e:
        error = f"Error fetching backup details: {e}"
    
    return render_template("backup_detail.html", active_tab='backups', backup=backup, error=error)

# ---------------------------------------------------------------------------
# Device CRUD proxies
# ---------------------------------------------------------------------------

@app.route('/add_device', methods=['POST'])
@login_required
def add_device():
    """Proxy for adding a device to the backend."""
    try:
        resp = api_request('POST', '/api/devices', json=request.get_json())
        return (resp.content, resp.status_code, resp.headers.items())
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500


@app.route('/approvals')
@login_required
def approvals():
    """Serve the approvals page"""
    return render_template('queue.html', active_tab='approvals')


# ---------------------------------------------------------------------------
# Baseline proposals proxies
# ---------------------------------------------------------------------------

@app.route('/api/baseline/proposals', methods=['GET'])
@login_required
def proposals_proxy():
    try:
        trailing = ('?' + request.query_string.decode()) if request.query_string else ''
        resp = api_request('GET', f"/api/baseline/proposals{trailing}")
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/baseline/proposals/<int:proposal_id>', methods=['PUT'])
@login_required
def decide_proposal_proxy(proposal_id):
    """Proxy for manually saving a baseline proposal to the backend."""
    try:
        resp = api_request('PUT', f'/api/baseline/proposals/{proposal_id}', json=request.get_json())
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.RequestException as e:
        try:
            error_json = e.response.json()
            return jsonify(error_json), e.response.status_code
        except (AttributeError, ValueError):
            return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Backups proxy
# ---------------------------------------------------------------------------

@app.route('/api/backups/save', methods=['POST'])
@login_required
def save_backup_proxy():
    """Proxy for manually saving a backup to the backend."""
    try:
        resp = api_request('POST', '/api/backups/save', json=request.get_json())
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.RequestException as e:
        try:
            error_json = e.response.json()
            return jsonify(error_json), e.response.status_code
        except (AttributeError, ValueError):
            return jsonify({'error': str(e)}), 500


@app.route('/device/delete/<string:device_name>', methods=['DELETE'])
@login_required
def delete_device(device_name):
    """Proxy for deleting a device from the backend."""
    try:
        resp = api_request('DELETE', f'/api/device/{device_name}')
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.RequestException as e:
        # Attempt to parse the error response from backend, or return a generic error
        try:
            error_json = e.response.json()
            return jsonify(error_json), e.response.status_code
        except (AttributeError, ValueError):
            return jsonify({'error': str(e)}), 500




@app.route('/devices')
@login_required
def devices():
    """Serve the devices page and display a list of devices"""
    devices_list = []
    error = None
    try:
        response = api_request('GET', '/api/devices')
        response.raise_for_status()  # Raise an exception for bad status codes
        devices_list = response.json()
    except requests.exceptions.RequestException as e:
        error = f"Error fetching devices: {e}"
    
    return render_template("devices.html", title="Devices - Net-Swift Orchestrator", active_tab='devices', devices=devices_list, error=error)



# ---------------------------------------------------------------------------
# Device query proxies
# ---------------------------------------------------------------------------

@app.route('/api/devices')
@login_required
def api_devices_proxy():
    """Proxy endpoint for fetching devices from backend"""
    try:
        response = api_request('GET', '/api/devices')
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/device/<string:device_name>')
@login_required
def api_device_proxy(device_name):
    """Proxy endpoint for fetching a single device from backend"""
    try:
        response = api_request('GET', f'/api/device/{device_name}')
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/device/<string:device_name>/status', methods=['PUT'])
@login_required
def api_update_device_status_proxy(device_name):
    """Proxy endpoint for updating device status"""
    try:
        response = api_request('PUT', f'/api/device/{device_name}/status', json=request.json)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Start local dev server
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(port=5051, debug=True, threaded=True)
