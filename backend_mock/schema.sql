-- Network Automation Database Schema

-- Device table to store network devices
CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    host TEXT NOT NULL,
    port INTEGER NOT NULL,
    status TEXT,
    device_type TEXT,
    platform TEXT
);

-- Backups table to store configuration backups
CREATE TABLE IF NOT EXISTS backups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device TEXT NOT NULL,
    command TEXT NOT NULL,
    method TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    content TEXT NOT NULL,
    size TEXT
);

-- Events table to store system events
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    type TEXT NOT NULL, -- e.g., 'status', 'retrieval', 'system'
    message TEXT NOT NULL
);

-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

-- Insert sample devices for testing
INSERT INTO devices (name, host, port, status, device_type, platform) VALUES
    ('R15', '172.16.39.102', 32783, 'unknown', 'router', 'cisco_ios'),
    ('SW1', '172.16.39.102', 32784, 'unknown', 'switch', 'cisco_ios'),
    ('SW2', '172.16.39.102', 32785, 'unknown', 'switch', 'cisco_ios');

-- Insert a test event
INSERT INTO events (timestamp, type, message) VALUES 
    (datetime('now'), 'system', 'Database initialized');
