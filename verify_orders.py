import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
db_config = {
    "host": os.environ.get('DB_HOST', "127.0.0.1"),
    "user": os.environ.get('DB_USER', "root"),
    "password": os.environ.get('DB_PASSWORD', "123"),
    "database": os.environ.get('DB_NAME', "skincare_shop")
}

def verify_and_fix_orders():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 1. Check table structure
        cursor.execute("DESCRIBE orders")
        columns = {col['Field']: col for col in cursor.fetchall()}
        
        print("Current orders table structure:")
        for col, info in columns.items():
            print(f"{col}: {info['Type']}")
            
        # 2. Verify total column exists and is DECIMAL
        if 'total' not in columns:
            print("\nAdding total column...")
            cursor.execute("ALTER TABLE orders ADD COLUMN total DECIMAL(10,2) NOT NULL DEFAULT 0.00")
        elif columns['total']['Type'] != 'decimal(10,2)':
            print("\nFixing total column type...")
            cursor.execute("ALTER TABLE orders MODIFY COLUMN total DECIMAL(10,2) NOT NULL DEFAULT 0.00")
            
        # 3. Check for NULL values in total
        cursor.execute("SELECT COUNT(*) as null_count FROM orders WHERE total IS NULL")
        null_count = cursor.fetchone()['null_count']
        if null_count > 0:
            print(f"\nFixing {null_count} NULL values in total column...")
            cursor.execute("UPDATE orders SET total = 0.00 WHERE total IS NULL")
            
        # 4. Show sample data
        cursor.execute("SELECT id, code, customer_id, total FROM orders LIMIT 5")
        print("\nSample orders data:")
        for row in cursor.fetchall():
            print(row)
            
        conn.commit()
        print("\nVerification and fixes completed successfully!")
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    verify_and_fix_orders() 