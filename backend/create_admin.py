#!/usr/bin/env python3
# Script to create admin user in the network_automation database

import sqlite3
import bcrypt
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('admin_creator')

def create_admin_user(username='admin', password='admin'):
    """Create an admin user with bcrypt-hashed password."""
    logger.info(f"Creating user: {username}")
    
    try:
        # Connect to database
        conn = sqlite3.connect('network_automation.db')
        c = conn.cursor()
        
        # Check if users table exists, create it if not
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        
        # Check if user already exists
        c.execute('SELECT username FROM users WHERE username = ?', (username,))
        existing_user = c.fetchone()
        
        if existing_user:
            # Update the existing user's password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            c.execute('UPDATE users SET password = ? WHERE username = ?', (hashed_password, username))
            logger.info(f"Updated existing user: {username}")
        else:
            # Create new user with hashed password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            logger.info(f"Created new user: {username}")
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        logger.info(f"Successfully set up user: {username}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
        return False

if __name__ == "__main__":
    success = create_admin_user()
    if success:
        print("\n✅ Admin user created/updated successfully")
        print("  Username: admin")
        print("  Password: admin")
    else:
        print("\n❌ Failed to create admin user")
