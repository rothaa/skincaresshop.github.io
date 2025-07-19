-- Drop existing order_items table if it exists
DROP TABLE IF EXISTS order_items;

-- Drop foreign keys from orders table
ALTER TABLE orders DROP FOREIGN KEY IF EXISTS orders_ibfk_2;

-- Drop product_id and qty columns from orders table if they exist
ALTER TABLE orders DROP COLUMN IF EXISTS product_id;
ALTER TABLE orders DROP COLUMN IF EXISTS qty;

-- Add order_date column if it doesn't exist
ALTER TABLE orders ADD COLUMN IF NOT EXISTS order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Create order_items table
CREATE TABLE order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id)
); 