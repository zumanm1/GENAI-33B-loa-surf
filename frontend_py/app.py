import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import requests
import os
import functools
import logging
from werkzeug.utils import secure_filename
from frontend_py.rag_processor import RAGProcessor

app = Flask(__name__, template_folder='templates')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'net_swift_frontend_secret_key')

# Configuration
BACKEND_API_URL = "http://127.0.0.1:5050"
AI_SERVICE_URL = "http://127.0.0.1:5052"
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'md'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the RAG Processor
# This will automatically fetch the AI config from the backend on startup.
rag_processor = RAGProcessor(docs_path=app.config['UPLOAD_FOLDER'])

def api_request(method, endpoint, **kwargs):
    """Make an authenticated request to the backend API."""
    url = f"{BACKEND_API_URL}{endpoint}"
    headers = kwargs.get('headers', {}) or {}
    if 'auth_token' in session:
        headers['Authorization'] = f"Bearer {session['auth_token']}"
    kwargs['headers'] = headers
    
    # Set a reasonable timeout to prevent hanging
    if 'timeout' not in kwargs:
        kwargs['timeout'] = 5  # 5 seconds timeout
    
    s = requests.Session()
    cookies = {}
    if 'auth_token' in session:
        cookies['auth_token'] = session['auth_token']
    if 'username' in session:
        cookies['username'] = session['username']
    
    for key, value in session.items():
        if key.startswith('backend_'):
            original_cookie_name = key[8:]
            cookies[original_cookie_name] = value
    
    if 'cookies' in kwargs:
        cookies.update(kwargs.pop('cookies'))
    
    for cookie_name, cookie_value in cookies.items():
        s.cookies.set(cookie_name, cookie_value)
    
    try:
        response = s.request(method, url, **kwargs)
        return response
    except requests.exceptions.ConnectionError:
        # Return a response-like object with error details
        class ErrorResponse:
            status_code = 503
            text = 'Backend service unavailable'
            def json(self):
                return {"error": "Backend service unavailable"}
            def raise_for_status(self):
                raise requests.exceptions.HTTPError("Backend service unavailable")
        return ErrorResponse()
    except requests.exceptions.Timeout:
        class TimeoutResponse:
            status_code = 504
            text = 'Backend request timed out'
            def json(self):
                return {"error": "Backend request timed out"}
            def raise_for_status(self):
                raise requests.exceptions.HTTPError("Backend request timed out")
        return TimeoutResponse()
    except requests.exceptions.RequestException as e:
        class GenericErrorResponse:
            status_code = 500
            text = f'Error connecting to backend: {str(e)}'
            def json(self):
                return {"error": f"Error connecting to backend: {str(e)}"}
            def raise_for_status(self):
                raise requests.exceptions.HTTPError(f"Error connecting to backend: {str(e)}")
        return GenericErrorResponse()

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

@app.context_processor
def inject_user():
    return dict(username=session.get('username'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET' and os.environ.get('DISABLE_AUTO_LOGIN') != 'true':
        if perform_auto_login():
            return redirect(url_for('index'))
    
    if 'username' in session and 'auth_token' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        try:
            s = requests.Session()
            try:
                response = s.post(f"{BACKEND_API_URL}/api/login", json={'username': username, 'password': password}, timeout=5)
                
                if response.status_code == 200:
                    # Handle empty response case explicitly
                    if not response.text.strip():
                        app.logger.error("Empty response received from backend")
                        flash("Backend returned an empty response. Service may be starting up. Please try again.", 'warning')
                        return render_template('login.html')
                        
                    try:
                        json_data = response.json()
                        session.clear()
                        session['username'] = json_data.get('username')
                        session['logged_in'] = True
                        session['auth_token'] = json_data.get('auth_token')
                        session['login_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        session['auto_login_attempts'] = 0  # Reset auto-login attempts
                        
                        resp = redirect(url_for('index'))
                        resp.set_cookie('auth_token', session['auth_token'], httponly=True, samesite='Strict', max_age=3600*24)
                        flash(f'Welcome back, {username}! You have successfully logged in.', 'success')
                        return resp
                    except ValueError as e:
                        app.logger.error(f"JSON parsing error: {str(e)}")
                        app.logger.error(f"Response content: '{response.text}'")
                        flash(f'Backend returned invalid JSON. The service may be starting up. Please try again in a moment.', 'warning')
                else:
                    # For non-200 responses
                    response_text = response.text.strip()
                    try:
                        if response_text:
                            error_message = response.json().get('error', 'Login failed.')
                        else:
                            error_message = f"Login failed (Status: {response.status_code}, empty response)"
                    except ValueError:
                        error_message = f"Login failed (Status: {response.status_code}, invalid response format)"
                    flash(error_message, 'danger')
            except requests.exceptions.ConnectionError:
                flash('Backend service is unavailable. Please try again later.', 'danger')
            except requests.exceptions.Timeout:
                flash('Backend request timed out. Please try again later.', 'danger')
            except requests.exceptions.RequestException as e:
                flash(f"Error connecting to backend: {str(e)}", 'danger')
        except Exception as e:
            app.logger.error(f"Unexpected error during login: {str(e)}")
            flash(f'An unexpected error occurred: {str(e)}', 'danger')
    return render_template('login.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/rag/upload', methods=['POST'])
@login_required
def upload_rag_document():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Re-process all documents in the upload folder
        try:
            success = rag_processor.process_documents()
            if success:
                return jsonify({'message': f'File "{filename}" uploaded and documents re-indexed successfully.'})
            else:
                return jsonify({'error': 'Failed to process documents after upload.'}), 500
        except Exception as e:
            logger.error(f"Error processing uploaded file: {e}")
            return jsonify({'error': 'Failed to process document.'}), 500

@app.route('/api/rag/query', methods=['POST'])
@login_required
def rag_query():
    data = request.get_json()
    query = data.get('query')
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    # Use the RAGProcessor instance to handle the query
    response = rag_processor.query(query)
    return jsonify({'response': response})

@app.route('/api/upload_document', methods=['POST'])
@login_required
def upload_document():
    if 'files[]' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    files = request.files.getlist('files[]')
    errors = []
    successful_uploads = []

    for file in files:
        if file.filename == '':
            continue
        if file and allowed_file(file.filename):
            filename = secrets.token_hex(8) + "_" + file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            try:
                with open(filepath, 'rb') as f:
                    ai_response = requests.post(
                        f"{AI_SERVICE_URL}/upload",
                        files={'file': (filename, f, file.mimetype)}
                    )
                    ai_response.raise_for_status()
                successful_uploads.append(filename)
            except requests.exceptions.RequestException as e:
                app.logger.error(f"AI service error for {filename}: {e}")
                errors.append(f"Error processing {filename}: Could not connect to AI service.")
            finally:
                if os.path.exists(filepath):
                    os.remove(filepath)
        else:
            errors.append(f'Invalid file type for {file.filename}')

    if errors:
        return jsonify({'error': '. '.join(errors)}), 500
    return jsonify({'message': 'Documents processed successfully.', 'filenames': successful_uploads})

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    data = request.json
    query = data.get('query')
    mode = data.get('mode')

    if not query:
        return jsonify({'error': 'Query is missing.'}), 400

    try:
        response = requests.post(f"{AI_SERVICE_URL}/chat", json={'query': query, 'query_type': mode})
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        app.logger.error(f"API error during chat processing: {e}")
        return jsonify({'error': 'Failed to communicate with AI service'}), 503
    except Exception as e:
        app.logger.error(f"Error during chat processing: {e}")
        return jsonify({'error': 'An error occurred during processing.'}), 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        try:
            response = requests.post(f"{BACKEND_API_URL}/api/register", json={'username': username, 'password': password})
            if response.status_code == 201:
                flash('Registration successful. Please log in.', 'success')
                return redirect(url_for('login'))
            else:
                flash(response.json().get('error', 'Registration failed.'), 'danger')
        except requests.exceptions.RequestException as e:
            flash(f"Error connecting to backend: {e}", 'danger')
    return render_template('register.html')

@app.route('/genai_networks_engineer')
@login_required
def genai_networks_engineer():
    return render_template('genai_networks_engineer.html', active_tab='genai_engineer')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

def perform_auto_login():
    # Check if auto-login is disabled via environment variable
    if os.environ.get('DISABLE_AUTO_LOGIN') == 'true':
        return False
        
    # Check for redirect loop prevention
    if session.get('auto_login_attempts', 0) > 3:
        session['auto_login_attempts'] = 0
        flash("Auto-login attempts exceeded, please login manually", "warning")
        return False
        
    if 'username' not in session:
        try:
            # Increment attempt counter to prevent infinite redirect loops
            session['auto_login_attempts'] = session.get('auto_login_attempts', 0) + 1
            
            s = requests.Session()
            try:
                response = s.post(
                    f"{BACKEND_API_URL}/api/login", 
                    json={'username': 'admin', 'password': 'admin'}, 
                    timeout=3
                )
                
                if response.status_code == 200:
                    # Check for empty response
                    if not response.text.strip():
                        app.logger.error("Empty response received from backend during auto-login")
                        flash("Backend returned an empty response. Please try again or login manually.", 'warning')
                        return False
                        
                    try:
                        json_data = response.json()
                        session['username'] = json_data.get('username')
                        session['logged_in'] = True
                        if 'auth_token' in json_data:
                            session['auth_token'] = json_data.get('auth_token')
                        for cookie in s.cookies:
                            session[f"backend_{cookie.name}"] = cookie.value
                        # Reset attempts counter on successful login
                        session['auto_login_attempts'] = 0
                        return True
                    except ValueError as e:
                        # JSON parsing error
                        app.logger.error(f"JSON parsing error during auto-login: {str(e)}")
                        app.logger.error(f"Response content: '{response.text}'")
                        flash("Backend returned invalid data. Please login manually.", "warning")
                        return False
                else:
                    flash(f"Backend error: {response.status_code}", "danger")
                    return False
                    
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                flash(f"Cannot connect to backend: {str(e)}", "danger")
                return False
                
        except Exception as e:
            # If any other error occurs, don't keep trying
            flash(f"Auto-login failed: {str(e)}", "danger")
            return False
            
    return 'username' in session

@app.route('/')
def index():
    if not perform_auto_login():
        return redirect(url_for('login'))
    
    try:
        dev_resp = api_request('GET', '/api/devices', timeout=3)
        dev_resp.raise_for_status()
        devices = dev_resp.json().get('devices', [])
    except requests.exceptions.RequestException:
        devices = []

    return render_template("index.html", devices=devices, total_devices=len(devices))

@app.route('/retrieve', methods=['GET', 'POST'])
@login_required
def retrieve():
    """Serve the config retrieve page and handle form submission"""
    devices_list = []
    try:
        response = api_request('GET', '/api/devices')
        response.raise_for_status()
        devices_list = response.json().get('devices', [])
    except requests.exceptions.RequestException as e:
        flash(f'Error fetching devices: {e}', 'danger')

    if request.method == 'POST':
        device_name = request.form.get('device')
        command = request.form.get('command')
        method = request.form.get('method')
        try:
            response = api_request('POST', '/api/retrieve', json={'device': device_name, 'command': command, 'method': method})
            response.raise_for_status()
            data = response.json()
            flash(f'Successfully retrieved config from {device_name}', 'success')
            return render_template('retrieve.html', devices=devices_list, last_output=data.get('output'), active_tab='retrieve')
        except requests.exceptions.RequestException as e:
            flash(f'Error: {e}', 'danger')

    return render_template('retrieve.html', devices=devices_list, active_tab='retrieve')

@app.route('/push', methods=['GET', 'POST'])
@login_required
def push():
    """Serve the config push page and handle form submission"""
    devices_list = []
    try:
        response = api_request('GET', '/api/devices')
        response.raise_for_status()
        devices_list = response.json().get('devices', [])
    except requests.exceptions.RequestException as e:
        flash(f'Error fetching devices: {e}', 'danger')

    if request.method == 'POST':
        device_name = request.form.get('device')
        config_data = request.form.get('config_data')
        try:
            response = api_request('POST', '/api/push', json={'device': device_name, 'config': config_data})
            response.raise_for_status()
            data = response.json()
            flash(f'Successfully pushed config to {device_name}', 'success')
            return render_template('push.html', devices=devices_list, last_output=data.get('output'), active_tab='push')
        except requests.exceptions.RequestException as e:
            flash(f'Error: {e}', 'danger')

    return render_template('push.html', devices=devices_list, active_tab='push')

@app.route('/backups')
@login_required
def backups():
    """Serve the backups page and display backup history"""
    backup_list = []
    try:
        response = api_request('GET', '/api/backups')
        response.raise_for_status()
        backup_list = response.json()
    except requests.exceptions.RequestException as e:
        flash(f'Error fetching backups: {e}', 'danger')
    return render_template('backups.html', backups=backup_list, active_tab='backups')

@app.route('/backup/<int:backup_id>')
@login_required
def backup_detail(backup_id):
    """Serve the backup detail page"""
    backup_data = None
    try:
        response = api_request('GET', f'/api/backup/{backup_id}')
        response.raise_for_status()
        backup_data = response.json()
    except requests.exceptions.RequestException as e:
        flash(f'Error fetching backup details: {e}', 'danger')
    return render_template('backup_detail.html', backup=backup_data, active_tab='backups')

@app.route('/devices', methods=['GET', 'POST'])
@login_required
def devices():
    if request.method == 'POST':
        # Handle add device
        device_data = {
            'name': request.form['name'],
            'ip': request.form['ip'],
            'device_type': request.form['device_type'],
            'username': request.form['username'],
            'password': request.form['password'],
        }
        try:
            response = api_request('POST', '/api/devices', json=device_data)
            response.raise_for_status()
            flash('Device added successfully!', 'success')
        except requests.exceptions.RequestException as e:
            flash(f'Error adding device: {e}', 'danger')
        return redirect(url_for('devices'))

    devices_list = []
    try:
        response = api_request('GET', '/api/devices')
        response.raise_for_status()
        devices_list = response.json().get('devices', [])
    except requests.exceptions.RequestException as e:
        flash(f'Error fetching devices: {e}', 'danger')
    
    return render_template('devices.html', devices=devices_list, active_tab='devices')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5051, debug=True)
