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

def update_database():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Drop foreign key constraint
        try:
            cursor.execute("ALTER TABLE orders DROP FOREIGN KEY orders_ibfk_2")
            print("Dropped foreign key constraint")
        except mysql.connector.Error as err:
            print(f"Note: Could not drop foreign key (might not exist): {err}")

        # Drop old columns from orders table
        try:
            cursor.execute("""
                ALTER TABLE orders 
                DROP COLUMN product_id,
                DROP COLUMN qty
            """)
            print("Dropped old columns")
        except mysql.connector.Error as err:
            print(f"Note: Could not drop columns (might not exist): {err}")

        # Add new columns to orders table
        try:
            cursor.execute("""
                ALTER TABLE orders 
                ADD COLUMN code VARCHAR(50) AFTER id,
                ADD COLUMN order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP AFTER customer_id
            """)
            print("Added new columns")
        except mysql.connector.Error as err:
            print(f"Note: Could not add columns (might already exist): {err}")

        # Create order_items table
        try:
            cursor.execute("""
                CREATE TABLE order_items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    order_id INT,
                    product_id INT,
                    quantity INT,
                    price DECIMAL(10,2),
                    FOREIGN KEY (order_id) REFERENCES orders(id),
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            """)
            print("Created order_items table")
        except mysql.connector.Error as err:
            print(f"Note: Could not create order_items table (might already exist): {err}")

        conn.commit()
        print("\nDatabase update completed successfully!")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        conn.close()

def ensure_total_column():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SHOW COLUMNS FROM orders LIKE 'total'")
    result = cursor.fetchone()
    if not result:
        cursor.execute("ALTER TABLE orders ADD COLUMN total DECIMAL(10,2)")
        print("Added 'total' column to 'orders' table.")
        conn.commit()
    else:
        print("'total' column already exists in 'orders' table.")
    cursor.close()
    conn.close()

def fix_null_totals():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET total = 0 WHERE total IS NULL")
    conn.commit()
    print("Set all NULL totals in orders table to 0.")
    cursor.close()
    conn.close()

def migrate_total_amount():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    # Check if total_amount column exists
    cursor.execute("SHOW COLUMNS FROM orders LIKE 'total_amount'")
    if cursor.fetchone():
        # Copy data from total_amount to total if total is NULL
        cursor.execute("UPDATE orders SET total = total_amount WHERE total IS NULL AND total_amount IS NOT NULL")
        # Drop the total_amount column
        cursor.execute("ALTER TABLE orders DROP COLUMN total_amount")
        print("Migrated data from total_amount to total and dropped total_amount column.")
        conn.commit()
    else:
        print("total_amount column does not exist; nothing to migrate.")
    cursor.close()
    conn.close()

def update_schema():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Check if total_amount column exists
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'orders' 
            AND COLUMN_NAME = 'total_amount'
        """, (db_config['database'],))
        
        has_total_amount = cursor.fetchone() is not None

        # Check if total column exists
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'orders' 
            AND COLUMN_NAME = 'total'
        """, (db_config['database'],))
        
        has_total = cursor.fetchone() is not None

        # Standardize on 'total' column
        if has_total_amount and not has_total:
            print("Renaming total_amount to total...")
            cursor.execute("ALTER TABLE orders CHANGE COLUMN total_amount total DECIMAL(10,2) NOT NULL")
        elif not has_total_amount and not has_total:
            print("Adding total column...")
            cursor.execute("ALTER TABLE orders ADD COLUMN total DECIMAL(10,2) NOT NULL DEFAULT 0")

        # Add subtotal column to order_items if it doesn't exist
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'order_items' 
            AND COLUMN_NAME = 'subtotal'
        """, (db_config['database'],))
        
        if cursor.fetchone() is None:
            print("Adding subtotal column to order_items...")
            cursor.execute("ALTER TABLE order_items ADD COLUMN subtotal DECIMAL(10,2) NOT NULL DEFAULT 0")

        # Update existing order_items subtotals
        print("Updating existing order_items subtotals...")
        cursor.execute("""
            UPDATE order_items 
            SET subtotal = price * quantity 
            WHERE subtotal = 0
        """)

        # Update order totals
        print("Updating order totals...")
        cursor.execute("""
            UPDATE orders o 
            SET total = (
                SELECT COALESCE(SUM(subtotal), 0) 
                FROM order_items oi 
                WHERE oi.order_id = o.id
            )
        """)

        conn.commit()
        print("Database schema updated successfully!")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    update_database()
    ensure_total_column()
    fix_null_totals()
    migrate_total_amount()
    update_schema() 