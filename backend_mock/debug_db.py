"""
Debug script to check database initialization and structure.
"""
import os
import sqlite3
from pathlib import Path

# Get the path to the database file
DB_PATH = Path(__file__).with_name("backend.db")

def check_db_exists():
    """Check if the database file exists."""
    if DB_PATH.exists():
        print(f"Database file exists at: {DB_PATH}")
        print(f"File size: {DB_PATH.stat().st_size} bytes")
        return True
    else:
        print(f"Database file does not exist at: {DB_PATH}")
        return False

def check_tables():
    """Check the structure of the database tables."""
    if not check_db_exists():
        return
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"\nTables in database: {[table['name'] for table in tables]}")
    
    # Check each table structure
    for table in tables:
        table_name = table['name']
        print(f"\nStructure of table '{table_name}':")
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col['name']} ({col['type']})")
    
    # Check if users table exists and has any records
    if any(table['name'] == 'users' for table in tables):
        cursor.execute("SELECT COUNT(*) as count FROM users;")
        user_count = cursor.fetchone()['count']
        print(f"\nNumber of users in database: {user_count}")
    
    conn.close()

def initialize_db():
    """Initialize the database with required tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
    """)
    
    # Create devices table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        host TEXT NOT NULL,
        port INTEGER NOT NULL,
        status TEXT,
        device_type TEXT,
        platform TEXT
    )
    """)
    
    # Create backups table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS backups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device TEXT NOT NULL,
        command TEXT NOT NULL,
        method TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        content TEXT NOT NULL,
        size TEXT
    )
    """)
    
    # Create events table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        type TEXT NOT NULL,
        message TEXT NOT NULL
    )
    """)
    
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == "__main__":
    print("Checking database status...")
    check_db_exists()
    check_tables()
    
    # Ask if user wants to reinitialize the database
    if DB_PATH.exists():
        choice = input("\nDo you want to delete and reinitialize the database? (y/n): ")
        if choice.lower() == 'y':
            try:
                os.remove(DB_PATH)
                print(f"Deleted existing database: {DB_PATH}")
                initialize_db()
                check_tables()
            except Exception as e:
                print(f"Error reinitializing database: {e}")
    else:
        print("\nInitializing new database...")
        initialize_db()
        check_tables()
