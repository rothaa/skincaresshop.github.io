#!/usr/bin/env python3
"""
Deployment setup script for Skincare Shop Backend
This script helps set up the database schema on Render
"""

import os
import mysql.connector
from dotenv import load_dotenv

def setup_database():
    """Set up the database schema"""
    load_dotenv()
    
    # Database connection parameters
    db_config = {
        "host": os.environ.get('DB_HOST', "127.0.0.1"),
        "user": os.environ.get('DB_USER', "root"),
        "password": os.environ.get('DB_PASSWORD', "123"),
        "database": os.environ.get('DB_NAME', "skincare_shop")
    }
    
    try:
        # Connect to database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        print("✅ Connected to database successfully!")
        
        # Read and execute SQL schema
        with open('skincareshop.sql', 'r') as file:
            sql_commands = file.read()
        
        # Split commands by semicolon and execute each
        commands = sql_commands.split(';')
        for command in commands:
            command = command.strip()
            if command:
                try:
                    cursor.execute(command)
                    print(f"✅ Executed: {command[:50]}...")
                except mysql.connector.Error as err:
                    if "already exists" not in str(err).lower():
                        print(f"⚠️  Warning: {err}")
        
        conn.commit()
        print("✅ Database schema setup completed!")
        
        # Create uploads directory if it doesn't exist
        uploads_dir = 'static/uploads'
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)
            print("✅ Created uploads directory")
        
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as err:
        print(f"❌ Database connection failed: {err}")
        print("Please check your environment variables:")
        print(f"DB_HOST: {os.environ.get('DB_HOST', 'Not set')}")
        print(f"DB_USER: {os.environ.get('DB_USER', 'Not set')}")
        print(f"DB_NAME: {os.environ.get('DB_NAME', 'Not set')}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Setting up Skincare Shop Backend Database...")
    success = setup_database()
    if success:
        print("🎉 Setup completed successfully!")
    else:
        print("💥 Setup failed. Please check the error messages above.") 