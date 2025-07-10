import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file, Response
import requests
import os
import functools
import logging
import datetime
import json
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

# Helper function to get document size
def get_file_size(file_path):
    """Get the size of a file in bytes."""
    try:
        return os.path.getsize(file_path)
    except Exception:
        return 0

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
    response = rag_processor.handle_query(query)
    return jsonify({'response': response})

@app.route('/api/ai/config', methods=['GET', 'POST'])
@login_required
def ai_config():
    if request.method == 'GET':
        try:
            # Forward the request to the backend to get the current config
            response = api_request('GET', '/api/ai/config')
            response.raise_for_status()  # Raise an exception for bad status codes
            return jsonify(response.json())
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching AI config from backend: {e}")
            return jsonify({'error': 'Failed to fetch AI configuration from backend.'}), 502

    if request.method == 'POST':
        try:
            new_config = request.get_json()
            # Forward the request to the backend to update the config
            response = api_request('POST', '/api/ai/config', json=new_config)
            response.raise_for_status()
            
            # After a successful update, tell the local RAG processor to reload its config
            rag_processor.reload_config()
            
            return jsonify(response.json())
        except requests.exceptions.RequestException as e:
            logger.error(f"Error updating AI config on backend: {e}")
            return jsonify({'error': 'Failed to update AI configuration on backend.'}), 502

@app.route('/api/upload_document', methods=['POST'])
@login_required
def upload_document():
    # Check if we're getting a regular form upload with files[] or a document with metadata
    if 'files[]' in request.files:
        # Handle multiple file uploads for the chat interface
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
                    if os.path.exists(filepath) and filename not in successful_uploads:
                        os.remove(filepath)
    
        if errors:
            return jsonify({'error': ', '.join(errors)}), 500
        
        return jsonify({'success': True, 'filenames': successful_uploads}), 200
    
    # Handle document management upload with metadata
    elif 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        # Check if the file extension is allowed
        if not '.' in file.filename or file.filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
            return jsonify({'error': f'Only {", ".join(ALLOWED_EXTENSIONS)} files are allowed'}), 400
        
        try:
            # Secure the filename and save the file
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Check if file already exists
            if os.path.exists(file_path):
                return jsonify({'error': 'A file with this name already exists'}), 409
                
            file.save(file_path)
            
            # Save metadata
            category = request.form.get('category', 'other')
            description = request.form.get('description', '')
            
            # Update document metadata in the RAG processor
            rag_processor.update_document_metadata(filename, {
                'category': category,
                'description': description,
                'upload_date': datetime.datetime.now().isoformat()
            })
            
            # Return success message
            return jsonify({'message': 'Document uploaded successfully', 'filename': filename}), 201
        except Exception as e:
            app.logger.error(f"Error uploading document: {e}")
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'No file part'}), 400

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
@login_required
def index():
    return redirect(url_for('config'))

@app.route('/config')
@login_required
def config():
    return render_template('genai_networks_engineer.html', page='config')

@app.route('/chat')
@login_required
def chat_page():
    return render_template('chat.html', page='chat')

@app.route('/documents')
@login_required
def documents_page():
    return render_template('documents.html', page='documents')

@app.route('/network-ops')
@login_required
def network_ops_page():
    return render_template('network_ops.html', page='network_ops')

@app.route('/analytics')
@login_required
def analytics_page():
    return render_template('analytics.html', page='analytics')

# Document management API endpoints
@app.route('/api/documents', methods=['GET'])
@login_required
def list_documents():
    """Get a list of all documents in the document store"""
    try:
        search = request.args.get('search', '')
        category = request.args.get('category', 'all')
        
        # Get all files in the upload directory
        docs_path = app.config['UPLOAD_FOLDER']
        documents = []
        total_size = 0
        
        for filename in os.listdir(docs_path):
            file_path = os.path.join(docs_path, filename)
            if os.path.isfile(file_path):
                # Get file metadata from the RAG processor if available
                doc_metadata = rag_processor.get_document_metadata(filename) or {}
                doc_category = doc_metadata.get('category', 'other')
                description = doc_metadata.get('description', '')
                
                # Apply filters
                if category != 'all' and doc_category != category:
                    continue
                    
                if search and search.lower() not in filename.lower() and search.lower() not in description.lower():
                    continue
                
                size = get_file_size(file_path)
                total_size += size
                
                documents.append({
                    'id': filename,
                    'filename': filename,
                    'size': size,
                    'upload_date': doc_metadata.get('upload_date', ''),
                    'category': doc_category,
                    'description': description
                })
        
        # Sort by most recent upload date
        documents.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
        
        return jsonify({
            'documents': documents,
            'total_documents': len(documents),
            'vector_store_size': rag_processor.get_vector_store_size()
        })
    except Exception as e:
        app.logger.error(f"Error listing documents: {e}")
        return jsonify({'error': str(e)}), 500

# The upload_document function has been consolidated with the existing one

@app.route('/api/documents/<document_id>', methods=['DELETE'])
@login_required
def delete_document(document_id):
    """Delete a document from the document store"""
    try:
        # Prevent directory traversal attacks
        filename = secure_filename(document_id)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({'error': 'Document not found'}), 404
            
        # Delete the file
        os.remove(file_path)
        
        # Remove document from the RAG processor
        rag_processor.delete_document(filename)
        
        return jsonify({'message': 'Document deleted successfully'}), 200
    except Exception as e:
        app.logger.error(f"Error deleting document: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/<document_id>/view', methods=['GET'])
@login_required
def view_document(document_id):
    """Return the document content for viewing"""
    try:
        # Prevent directory traversal attacks
        filename = secure_filename(document_id)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({'error': 'Document not found'}), 404
        
        # For binary files like PDFs, serve the file directly
        if filename.endswith('.pdf'):
            return send_file(file_path, mimetype='application/pdf')
        
        # For text files, read and return the content
        with open(file_path, 'r') as f:
            content = f.read()
        
        return jsonify({
            'filename': filename,
            'content': content
        })
    except Exception as e:
        app.logger.error(f"Error viewing document: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/reindex', methods=['POST'])
@login_required
def reindex_documents():
    """Force reindex of all documents in the vector store"""
    try:
        # Reset the vector store in the RAG processor
        rag_processor.reset_vector_store()
        
        return jsonify({'message': 'Vector store reindexed successfully'}), 200
    except Exception as e:
        app.logger.error(f"Error reindexing documents: {e}")
        return jsonify({'error': str(e)}), 500

# Network Operations API endpoints
@app.route('/api/devices', methods=['GET'])
@login_required
def list_devices():
    """Get list of network devices"""
    try:
        search = request.args.get('search', '')
        # Forward request to backend
        response = api_request('GET', '/api/devices')
        
        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch devices'}), response.status_code
            
        devices = response.json()
        
        # Apply search filter if provided
        if search:
            devices = [d for d in devices if search.lower() in d.get('hostname', '').lower() 
                      or search.lower() in d.get('ip_address', '').lower()
                      or search.lower() in d.get('device_type', '').lower()]
        
        return jsonify(devices), 200
    except Exception as e:
        app.logger.error(f"Error listing devices: {e}")
        return jsonify({'error': str(e)}), 500
        
@app.route('/api/devices', methods=['POST'])
@login_required
def add_device():
    """Add a new network device"""
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Forward request to backend
        response = api_request('POST', '/api/devices', json=data)
        
        if response.status_code not in [200, 201]:
            return jsonify(response.json()), response.status_code
            
        return jsonify(response.json()), response.status_code
    except Exception as e:
        app.logger.error(f"Error adding device: {e}")
        return jsonify({'error': str(e)}), 500
        
@app.route('/api/devices/<hostname>', methods=['GET'])
@login_required
def get_device(hostname):
    """Get details for a specific network device"""
    try:
        # Forward request to backend
        response = api_request('GET', f'/api/devices/{hostname}')
        
        if response.status_code != 200:
            return jsonify({'error': f'Failed to fetch device: {hostname}'}), response.status_code
            
        return jsonify(response.json()), 200
    except Exception as e:
        app.logger.error(f"Error getting device details: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/<hostname>/stats', methods=['GET'])
@login_required
def get_device_stats(hostname):
    """Get statistics for a specific network device"""
    try:
        # Forward request to backend
        response = api_request('GET', f'/api/devices/{hostname}/stats')
        
        if response.status_code != 200:
            return jsonify({'error': f'Failed to fetch stats for device: {hostname}'}), response.status_code
            
        return jsonify(response.json()), 200
    except Exception as e:
        app.logger.error(f"Error getting device stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/proposals', methods=['GET'])
@login_required
def list_proposals():
    """Get list of configuration proposals"""
    try:
        # Get filter parameters
        device = request.args.get('device', '')
        status = request.args.get('status', '')
        
        # Forward request to backend
        endpoint = '/api/proposals'
        params = {}
        if device:
            params['device'] = device
        if status:
            params['status'] = status
            
        response = api_request('GET', endpoint, params=params)
        
        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch proposals'}), response.status_code
            
        return jsonify(response.json()), 200
    except Exception as e:
        app.logger.error(f"Error listing proposals: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/proposals', methods=['POST'])
@login_required
def create_proposal():
    """Create a new configuration proposal"""
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Add username from session
        data['user'] = session.get('username', 'unknown')
        
        # Forward request to backend
        response = api_request('POST', '/api/proposals', json=data)
        
        if response.status_code not in [200, 201]:
            return jsonify(response.json()), response.status_code
            
        return jsonify(response.json()), response.status_code
    except Exception as e:
        app.logger.error(f"Error creating proposal: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/proposals/<id>/approve', methods=['POST'])
@login_required
def approve_proposal(id):
    """Approve a configuration proposal"""
    try:
        # Forward request to backend
        response = api_request('POST', f'/api/proposals/{id}/approve')
        
        if response.status_code != 200:
            return jsonify({'error': f'Failed to approve proposal {id}'}), response.status_code
            
        return jsonify(response.json()), 200
    except Exception as e:
        app.logger.error(f"Error approving proposal: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/proposals/<id>/reject', methods=['POST'])
@login_required
def reject_proposal(id):
    """Reject a configuration proposal"""
    try:
        # Get reason from request data
        data = request.get_json() or {}
        reason = data.get('reason', '')
        
        # Forward request to backend
        response = api_request('POST', f'/api/proposals/{id}/reject', json={'reason': reason})
        
        if response.status_code != 200:
            return jsonify({'error': f'Failed to reject proposal {id}'}), response.status_code
            
        return jsonify(response.json()), 200
    except Exception as e:
        app.logger.error(f"Error rejecting proposal: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/network/ai', methods=['POST'])
@login_required
def network_ai_chat():
    """Send a query to the network AI assistant"""
    try:
        # Get request data
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'No query provided'}), 400
            
        query = data['query']
        device = data.get('device', '')
        
        # Forward request to AI service
        payload = {'query': query, 'query_type': 'network'}
        if device:
            payload['device'] = device
            
        response = requests.post(f"{AI_SERVICE_URL}/chat", json=payload)
        response.raise_for_status()
        
        return jsonify(response.json()), 200
    except requests.exceptions.RequestException as e:
        app.logger.error(f"API error during network AI chat: {e}")
        return jsonify({'error': 'Failed to communicate with AI service'}), 503
    except Exception as e:
        app.logger.error(f"Error processing network AI query: {e}")
        return jsonify({'error': str(e)}), 500

# Analytics API endpoints
@app.route('/api/analytics', methods=['GET'])
@login_required
def get_analytics():
    """Get network analytics data"""
    try:
        # Get time range parameters
        time_range = request.args.get('time_range', 'day')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        
        # Forward request to backend
        endpoint = '/api/analytics'
        params = {'time_range': time_range}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
            
        response = api_request('GET', endpoint, params=params)
        
        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch analytics data'}), response.status_code
            
        return jsonify(response.json()), 200
    except Exception as e:
        app.logger.error(f"Error getting analytics data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/export', methods=['GET'])
@login_required
def export_analytics():
    """Export analytics data as CSV"""
    try:
        # Get time range parameters
        time_range = request.args.get('time_range', 'day')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        
        # Forward request to backend
        endpoint = '/api/analytics/export'
        params = {'time_range': time_range}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
            
        response = api_request('GET', endpoint, params=params)
        
        if response.status_code != 200:
            return jsonify({'error': 'Failed to export analytics data'}), response.status_code
            
        # Create a response with the CSV data
        csv_data = response.text
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        filename = f"network_analytics_{current_date}.csv"
        
        # Create a response with the CSV data
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    except Exception as e:
        app.logger.error(f"Error exporting analytics data: {e}")
        return jsonify({'error': str(e)}), 500

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
