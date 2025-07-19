import mysql.connector
from mysql.connector import errorcode
import os
# from dotenv import load_dotenv # Temporarily disabling dotenv
# from pathlib import Path

# Explicitly load the .env file from the project directory
# env_path = Path('.') / '.env'
# load_dotenv(dotenv_path=env_path)

# --- TEMPORARY DEBUGGING ---
# Using direct credentials to bypass the .env loading issue.
config = {
    'user': 'root',
    'password': '123',
    'host': '127.0.0.1',
    'database': 'skincare_shop',
}

print("Attempting to set up the database with direct credentials...")

try:
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()

    with open('skincareshop.sql', 'r') as f:
        sql_script = f.read()

    # The setup script from Render's MySQL doesn't like the CREATE DATABASE or USE commands
    # when the database is already specified in the connection.
    # We will remove them from the script before executing.
    sql_commands = sql_script.split(';')
    
    # Filter out CREATE DATABASE and USE commands
    filtered_commands = [
        cmd for cmd in sql_commands 
        if cmd.strip() and not cmd.strip().upper().startswith('CREATE DATABASE') and not cmd.strip().upper().startswith('USE')
    ]

    for command in filtered_commands:
        if command.strip():
            try:
                cursor.execute(command)
            except mysql.connector.Error as err:
                # If the table already exists, we can ignore the error
                if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                    print(f"Ignoring error: {err}")
                else:
                    raise

    # Add columns to products table if they don't exist, or modify if they do
    try:
        print("Checking for missing columns in 'products' table...")
        # Try to add the columns first
        cursor.execute("""
            ALTER TABLE products
            ADD COLUMN image_url TEXT,
            ADD COLUMN category VARCHAR(255)
        """)
        print("Added 'image_url' and 'category' columns to 'products' table.")
    except mysql.connector.Error as err:
        # Error 1060 is for "Duplicate column name"
        if err.errno == 1060:
            print("Columns already exist, modifying them instead.")
            # If columns exist, modify them to ensure correct type
            cursor.execute("ALTER TABLE products MODIFY COLUMN image_url TEXT")
            cursor.execute("ALTER TABLE products MODIFY COLUMN category VARCHAR(255)")
            print("Modified 'image_url' and 'category' columns.")
        else:
            raise

    print("Database setup complete.")
    cnx.commit()

except mysql.connector.Error as err:
    print(f"Database setup failed: {err}")
finally:
    if 'cnx' in locals() and cnx.is_connected():
        cursor.close()
        cnx.close()
        print("MySQL connection closed.")