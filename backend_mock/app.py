"""Lightweight mock backend service for Net-Swift Orchestrator

This service implements the minimal set of API endpoints expected by the
Flask+Bootstrap frontend.  It purposefully avoids heavy network-automation
libraries so that it can run with a basic Python + Flask installation.

The goal is to let you demo / develop the UI without needing actual network
hardware.  All data are stored in-memory so the state resets whenever the
process restarts.
"""
from __future__ import annotations

from datetime import datetime, timezone
from itertools import count
from typing import Dict, List
import sqlite3
import subprocess
import socket
from pathlib import Path
import sys
import json

# Ensure project root is on sys.path so sibling packages can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
import secrets
import functools
from flask import Flask, jsonify, request, session, make_response
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

# ---------------------------------------------------------------------------
# Baseline management subsystem (new)
# ---------------------------------------------------------------------------
from baseline_core import init_db as baseline_init_db
from baseline_core.diff import diff_and_record
from baseline_core.routes import bp as baseline_bp

app = Flask(__name__)
# Register baseline blueprint under existing /api namespace
app.register_blueprint(baseline_bp, url_prefix="/api")
CORS(app)
app.secret_key = secrets.token_hex(16)

# ---------------------------------------------------------------------------
# In-memory data stores
# ---------------------------------------------------------------------------
_device_id_counter = count(1)

# Use a file-based cache for status overrides to ensure it's shared across requests/threads
OVERRIDE_CACHE_PATH = Path(__file__).parent / 'status_overrides.json'

def _get_override_cache() -> Dict[str, str]:
    if not OVERRIDE_CACHE_PATH.exists():
        return {}
    try:
        with open(OVERRIDE_CACHE_PATH, 'r') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError):
        return {}

def _set_override_cache(overrides: Dict[str, str]):
    try:
        with open(OVERRIDE_CACHE_PATH, 'w') as f:
            json.dump(overrides, f)
    except IOError:
        pass # Fail silently if cache can't be written



def _ts() -> str:
    """Return current timestamp as ISO string."""
    return datetime.now(timezone.utc).isoformat()

DB_PATH = Path(__file__).with_name("backend.db")

# ---------------------------------------------------------------------------
# SQLite helpers

def get_db_path():
    """Get database path from app config or use default."""
    return app.config.get('DATABASE', DB_PATH)

def _get_conn():
    """Get a new SQLite connection with WAL and a longer busy timeout to avoid locking."""
    conn = sqlite3.connect(get_db_path(), timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Improve concurrency
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")  # 30 seconds
    return conn

def _find_device(name: str):
    """Return device row dict by name or None."""
    conn = _get_conn()
    cur = conn.execute("SELECT * FROM devices WHERE name=?", (name,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

# ---------------------------------------------------------------------------

PING_HOST = "172.16.39.102"


def _ping_eve() -> bool:
    try:
        result = subprocess.run(["ping", "-c", "1", "-W", "1", PING_HOST], stdout=subprocess.DEVNULL)
        return result.returncode == 0
    except Exception:
        return False


def _update_statuses(device_id=None):
    # For test runs, allow disabling automatic status refresh to avoid race conditions
    if os.getenv('DISABLE_AUTO_STATUS') == '1':
        return
    """Update device statuses.
    
    Args:
        device_id: If provided, only update this specific device.
    """
    if not _ping_eve():
        return  # if gateway unreachable keep statuses

    conn = _get_conn()
    
    # Query either all devices or a specific one
    if device_id:
        cur = conn.execute("SELECT id, name, host, port, status FROM devices WHERE id = ?", (device_id,))
    else:
        cur = conn.execute("SELECT id, name, host, port, status FROM devices")
        
    rows = cur.fetchall()
    status_changes = []
    
    for r in rows:
        # Skip devices that have a status override set by a test
        if r["name"] in _get_override_cache():
            continue

        old_status = r["status"]
        try:
            with socket.create_connection((r["host"], r["port"]), timeout=2):
                new_status = "online"
        except Exception:
            new_status = "offline"

        if old_status != new_status:
            conn.execute("UPDATE devices SET status = ? WHERE id = ?", (new_status, r["id"]))
            status_changes.append({
                "device_id": r["id"],
                "device_name": r["name"],
                "old_status": old_status,
                "new_status": new_status
            })

    # Commit all status updates before issuing separate log writes to avoid write lock contention
    conn.commit()
    conn.close()

    for change in status_changes:
        _log_event(
            "status",
            f"Device {change['device_name']} changed status from {change['old_status']} to {change['new_status']}.",
        )

    # Return status changes for potential real-time updates
    return status_changes



def init_db():
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            host TEXT NOT NULL,
            port INTEGER NOT NULL,
            status TEXT,
            device_type TEXT,
            platform TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS backups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device TEXT NOT NULL,
            command TEXT NOT NULL,
            method TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            content TEXT NOT NULL,
            size TEXT
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            type TEXT NOT NULL, -- e.g., 'status', 'retrieval', 'system'
            message TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
        """
    )
    conn.commit()

    # Seed if empty
    cur.execute("SELECT COUNT(*) FROM devices")
    if cur.fetchone()[0] == 0:
        seed = [
            ("R15", "172.16.39.102", 32783),
            ("R16", "172.16.39.102", 32773),
            ("R17", "172.16.39.102", 32785),
            ("R18", "172.16.39.102", 32786),
            ("R19", "172.16.39.102", 32771),
            ("R20", "172.16.39.102", 32788),
        ]
        cur.executemany(
            "INSERT INTO devices (name, host, port, status, device_type, platform) VALUES (?,?,?,?,?,?)",
            [(n, h, p, "online", "cisco_ios_telnet", "ios") for n, h, p in seed],
        )
        conn.commit()
    conn.close()

# ---------------------------------------------------------------------------
# Helper functions

def _save_backup(device: str, command: str, method: str, content: str) -> int:
    """Insert into backups table and run deviation diff check."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO backups (device, command, method, timestamp, content, size)
           VALUES (?,?,?,?,?,?)""",
        (
            device,
            command,
            method,
            _ts(),
            content,
            len(content.encode()),
        ),
    )
    backup_id = cur.lastrowid
    conn.commit()
    conn.close()

    # Run baseline deviation detection (non-blocking; ignore errors)
    try:
        device_row = _find_device_row(device)
        if device_row:
            diff_and_record(device_row["id"], content)
    except Exception as exc:  # noqa: BLE001
        print(f"[WARN] deviation diff failed: {exc}")
    return backup_id
# ---------------------------------------------------------------------------

def _find_device_row(name: str):
    conn = _get_conn()
    cur = conn.execute("SELECT * FROM devices WHERE name = ?", (name,))
    row = cur.fetchone()
    conn.close()
    return row

def _log_event(event_type: str, message: str):
    """Adds an event to the events table."""
    conn = _get_conn()
    conn.execute(
        "INSERT INTO events (timestamp, type, message) VALUES (?, ?, ?)",
        (_ts(), event_type, message),
    )
    conn.commit()
    conn.close()

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Authentication Decorator
# ---------------------------------------------------------------------------

def login_required(view):
    """View decorator that requires a user to be logged in."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        # Check for session-based authentication
        if "user_id" in session:
            return view(**kwargs)
            
        # Check for token-based authentication
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            print(f"Received auth token: {token[:10]}...")
            
            # For demo purposes, accept any non-empty token
            # In a real app, you would validate the token against a database
            if token:
                return view(**kwargs)
        
        # No valid authentication found
        return jsonify({"error": "Authentication required"}), 401
    return wrapped_view


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@app.route("/api/register", methods=["POST"])
def register():
    """Register a new user."""
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400

    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, generate_password_hash(password)),
        )
        conn.commit()
        _log_event("auth", f"User '{username}' registered successfully.")
        return jsonify({"message": "User registered successfully."}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": f"Username '{username}' is already taken."}), 409
    finally:
        conn.close()


@app.route("/api/login", methods=["POST"])
def login():
    """Log a user in by establishing a session."""
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400

    conn = _get_conn()
    user_row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()

    if user_row and check_password_hash(user_row["password_hash"], password):
        session.clear()
        session["user_id"] = user_row["id"]
        session["username"] = user_row["username"]
        
        # Generate an auth token
        import hashlib
        import time
        auth_token = hashlib.sha256(f"{username}:{user_row['id']}:{time.time()}:{secrets.token_hex(16)}".encode()).hexdigest()
        
        _log_event("auth", f"User '{username}' logged in.")
        
        # Debug print session data
        print(f"Backend session after login: {session}")
        print(f"Generated auth token: {auth_token[:10]}...")
        
        response = jsonify({
            "message": "Login successful.", 
            "username": user_row["username"],
            "auth_token": auth_token
        })
        return response
    
    _log_event("auth", f"Failed login attempt for user '{username}'.")    
    return jsonify({"error": "Invalid username or password."}), 401


@app.route("/api/logout", methods=["POST"])
@login_required
def logout():
    """Log the current user out."""
    username = session.get("username", "unknown user")
    session.clear()
    _log_event("auth", f"User '{username}' logged out.")
    return jsonify({"message": "Logout successful."})


@app.route("/api/devices", methods=["GET", "POST"])
@login_required
def devices_collection():
    if request.method == "GET":
        # Disabled automatic status refresh to ensure deterministic tests
        # _update_statuses()
        conn = _get_conn()
        cur = conn.execute("SELECT * FROM devices")
        devices = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify(devices)

    # POST – add device
    data = request.get_json(force=True)
    name, host, port = data.get("name"), data.get("host"), data.get("port")
    if not all([name, host, port]):
        return jsonify({"error": "'name', 'host' and 'port' required"}), 400

    try:
        conn = _get_conn()
        cur = conn.execute(
            "INSERT INTO devices (name, host, port, status, device_type, platform) VALUES (?,?,?,?,?,?)",
            (name, host, int(port), "unknown", "cisco_ios_telnet", "ios"),
        )
        conn.commit()
        device_id = cur.lastrowid
        conn.close()
        return jsonify({"id": device_id, "name": name, "host": host, "port": int(port), "status": "unknown", "device_type": "cisco_ios_telnet", "platform": "ios"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": f"device '{name}' already exists"}), 409


@app.route("/api/devices/<int:device_id>", methods=["PUT", "DELETE"])
@login_required
def device_item(device_id: int):
    if request.method == "PUT":
        data = request.get_json(force=True)
        fields = [
            ("name", data.get("name")),
            ("host", data.get("host")),
            ("port", data.get("port")),
            ("status", data.get("status")),
        ]
        sets = ", ".join([f"{k} = ?" for k, v in fields if v is not None])
        values = [v for k, v in fields if v is not None]
        if not sets:
            return jsonify({"error": "no fields to update"}), 400
        values.append(device_id)
        conn = _get_conn()
        conn.execute(f"UPDATE devices SET {sets} WHERE id = ?", values)
        conn.commit()
        conn.close()
        return jsonify({"status": "updated"})

    # DELETE
    conn = _get_conn()
    conn.execute("DELETE FROM devices WHERE id = ?", (device_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})


@app.route("/api/config/retrieve", methods=["POST"])
@login_required
def config_retrieve():
    """Return fake command output and create a backup entry."""
    data = request.get_json(force=True)
    device = data.get("device")
    command = data.get("command")
    method = data.get("method", "netmiko")
    mode = data.get("mode", "mock")

    if not device or not command:
        return jsonify({"error": "'device' and 'command' are required"}), 400

    device_obj = _find_device(device)
    if not device_obj:
        return jsonify({"error": f"device '{device}' not found"}), 404

    if mode == "live":
        try:
            if method == "netmiko":
                try:
                    from netmiko import ConnectHandler  # type: ignore
                    conn = ConnectHandler(
                        device_type="cisco_ios_telnet",
                        host=device_obj["host"],
                        port=int(device_obj["port"]),
                        username="cisco",
                        password="cisco",
                        fast_cli=False,
                    )
                    output = conn.send_command(command, expect_string=r"[#>]", strip_prompt=False, strip_command=False)
                    conn.disconnect()
                except ImportError:
                    return jsonify({"error": "Netmiko library not found. Please run 'pip install netmiko'."}), 500
            elif method == "napalm":
                try:
                    from napalm import get_network_driver  # type: ignore
                    driver = get_network_driver("ios")
                    device_conn = driver(
                        hostname=device_obj["host"],
                        username="cisco",
                        password="cisco",
                        optional_arguments={"port": int(device_obj["port"]), "transport": "telnet"},
                    )
                    device_conn.open()
                    output_dict = device_conn.cli([command])
                    output = output_dict.get(command, "")
                    device_conn.close()
                except ImportError:
                    return jsonify({"error": "NAPALM library not found. Please run 'pip install napalm'."}), 500
            else:
                return jsonify({"error": f"Unsupported connection method: {method}. Use 'netmiko' or 'napalm'."}), 400
        except Exception as exc:
            return jsonify({"error": f"live retrieval failed: {exc}"}), 500
    else:
        output = f"[MOCK] {device}> {command}\nSample output generated at {_ts()}"
    _log_event("retrieval", f"Retrieved mock config from {device} for command: '{command[:20]}...'")

    # Save backup & run deviation detection
    _save_backup(device, command, method, output)

    return jsonify({"device": device, "command": command, "content": output})


@app.route("/api/backups/save", methods=["POST"])
@login_required
def save_backup_manually():
    """Saves a configuration to the backups table manually."""
    data = request.get_json()
    device = data.get("device")
    command = data.get("command")
    method = data.get("method")
    content = data.get("content")

    if not all([device, command, method, content]):
        return jsonify({"error": "Missing required data for backup."}), 400

    backup_id = _save_backup(device, command, method, content)
    _log_event("system", f"User manually saved backup {backup_id} for device {device}.")

    return jsonify({"message": "Backup saved successfully.", "backup_id": backup_id}), 201


def _push_config_live(device_name: str, commands: list[str]) -> str:
    """Pushes a list of configuration commands to a device using Netmiko."""
    device_row = _find_device_row(device_name)
    if not device_row:
        raise ValueError(f"Device '{device_name}' not found in database.")

    cisco_device = {
        "device_type": "cisco_ios_telnet",
        "host": device_row["host"],
        "port": device_row["port"],
        "username": "cisco",
        "password": "cisco",
        "secret": "cisco",
    }

    try:
        from netmiko import ConnectHandler
        from netmiko.exceptions import NetmikoAuthenticationException, NetmikoTimeoutException

        with ConnectHandler(**cisco_device) as net_connect:
            net_connect.enable()
            output = net_connect.send_config_set(commands)
            net_connect.save_config()
            return output
    except ImportError:
        raise RuntimeError("Netmiko library is not installed. Cannot perform live push.")
    except NetmikoAuthenticationException:
        raise ConnectionRefusedError(f"Authentication failed for {device_name}.")
    except NetmikoTimeoutException:
        raise ConnectionAbortedError(f"Connection timed out for {device_name}.")
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred: {e}")


@app.route("/api/config/push", methods=["POST"])
@login_required
def config_push():
    """Pushes a configuration to a device."""
    data = request.get_json()
    device = data.get("device")
    commands = data.get("commands")
    mode = data.get("mode", "mock")

    if not all([device, commands]):
        return jsonify({"error": "'device' and 'commands' are required."}), 400

    if mode == "live":
        try:
            output = _push_config_live(device, commands)
            _log_event("push", f"Successfully pushed live config to {device}.")
        except Exception as e:
            _log_event("error", f"Live push to {device} failed: {e}")
            return jsonify({"error": f"Live push failed: {e}"}), 500
    else:
        output_lines = [f"{device}(config)# {cmd}" for cmd in commands]
        output = "\n".join(output_lines)
        _log_event("push", f"Pushed mock config to {device}.")

    return jsonify({"output": output})


@app.route("/api/backups", methods=["GET"])
@login_required
def list_backups():
    conn = _get_conn()
    cur = conn.execute("SELECT * FROM backups ORDER BY id DESC")
    backups = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(backups)


@app.route("/api/backup/<int:backup_id>", methods=["GET"])
@login_required
def get_backup(backup_id: int):
    """Return a specific backup entry."""
    conn = _get_conn()
    cur = conn.execute("SELECT * FROM backups WHERE id = ?", (backup_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return jsonify(dict(row))
    return jsonify({"error": "backup not found"}), 404


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "timestamp": _ts()})


@app.route("/api/device/<string:device_name>", methods=["GET"])
@login_required
def get_device(device_name: str):
    """Return a specific device by name."""
    # Removed automatic status refresh to avoid race conditions in tests
    # _update_statuses()
    
    conn = _get_conn()
    cur = conn.execute("SELECT * FROM devices WHERE name = ?", (device_name,))
    row = cur.fetchone()
    conn.close()
    
    if row:
        device = dict(row)
        # If a test has set a status override, return that instead of the DB value
        overrides = _get_override_cache()
        if device["name"] in overrides:
            device["status"] = overrides[device["name"]]
        return jsonify(device)
    return jsonify({"error": "device not found"}), 404


@app.route("/api/device/<string:device_name>/status", methods=["PUT"])
@login_required
def update_device_status(device_name: str):
    """Update a device's status."""
    data = request.get_json()
    new_status = data.get("status")
    
    if not new_status or new_status not in ["online", "offline", "unknown"]:
        return jsonify({"error": "Valid status required (online, offline, or unknown)"}), 400
    
    conn = _get_conn()
    
    # First check if device exists
    cur = conn.execute("SELECT id, status FROM devices WHERE name = ?", (device_name,))
    row = cur.fetchone()
    
    if not row:
        conn.close()
        return jsonify({"error": "device not found"}), 404
    
    device_id = row["id"]
    old_status = row["status"]
    
    # Only update if status changed
    if old_status != new_status:
        conn.execute("UPDATE devices SET status = ? WHERE id = ?", (new_status, device_id))
        conn.commit()
        
        db_conn.commit()
    db_conn.close()

    # Add to overrides to protect from background updates during tests
    overrides = _get_override_cache()
    overrides[device_name] = new_status
    _set_override_cache(overrides)

    _log_event(
        "status",
        f"Device {device_name} status updated to {new_status} by user {session.get('username', 'unknown')}.",
    )

    return jsonify({"name": device_name, "status": new_status})


@app.route("/api/device/delete/<string:device_name>", methods=["DELETE"])
@login_required
def delete_device(device_name: str):
    """Deletes a device from the database."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM devices WHERE name = ?", (device_name,))
    device = cur.fetchone()

    if not device:
        conn.close()
        return jsonify({"error": f"Device '{device_name}' not found."}), 404

    cur.execute("DELETE FROM devices WHERE name = ?", (device_name,))
    conn.commit()
    conn.close()

    _log_event("system", f"Device '{device_name}' has been deleted.")
    return jsonify({"message": f"Device '{device_name}' deleted successfully."})


@app.route("/api/events", methods=["GET"])
@login_required
def get_events():
    """Return the last 10 system events."""
    conn = _get_conn()
    cur = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT 10")
    events = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(events)

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Root route for quick health / friendliness
# ---------------------------------------------------------------------------

@app.route("/")
def index_root():
    return jsonify({"message": "Net-Swift Orchestrator backend running.", "docs": "/api/health"})

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    init_db()  # Initialize the database
    _log_event("system", "Backend application started.")
    # Initialise baseline.db (idempotent)
    baseline_init_db()
    app.run(host="0.0.0.0", port=5050, debug=True, use_reloader=False)
