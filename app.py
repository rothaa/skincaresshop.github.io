from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
import mysql.connector
from mysql.connector import pooling
from functools import wraps
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import secrets
import time
import csv
import io


load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'you-should-definitely-change-this')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# --- Login System ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        if user:
            flash('Username already exists. Please choose another.', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('register'))
            
        password_hash = generate_password_hash(password)
        
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, password_hash))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['logged_in'] = True
            session['user_id'] = user['id']
            session['username'] = user['username']
            # session['role'] is no longer stored
            flash('You were successfully logged in.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You were logged out.', 'success')
    return redirect(url_for('index'))

# --- Database ---
# MySQL connection pooling
db_config = {
    "host": os.environ.get('DB_HOST', "127.0.0.1"),
    "user": os.environ.get('DB_USER', "root"),
    "password": os.environ.get('DB_PASSWORD', "123"),
    "database": os.environ.get('DB_NAME', "skincare_shop"),
    "pool_name": "skincare_pool",
    "pool_size": 20,  # Increased from 5 to 20
    "pool_reset_session": True  # Reset session variables when returning to pool
}

try:
    cnx_pool = mysql.connector.pooling.MySQLConnectionPool(**db_config)
except mysql.connector.Error as err:
    print(f"FATAL: Database connection failed: {err}")
    print("Please ensure the database is running and the credentials in your .env file are correct.")
    cnx_pool = None

def get_db_connection():
    """Get a connection from the pool."""
    if cnx_pool is None:
        raise RuntimeError("Database connection is not available.")
    try:
        return cnx_pool.get_connection()
    except mysql.connector.errors.PoolError:
        # If pool is exhausted, wait a bit and try again
        time.sleep(0.1)
        return cnx_pool.get_connection()

def close_db_connection(conn, cursor=None):
    """Safely close database cursor and connection."""
    try:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    except Exception as e:
        print(f"Error closing database connection: {e}")

# Before running, ensure you have created the following MySQL tables:
#
# CREATE TABLE products (
#   id INT AUTO_INCREMENT PRIMARY KEY,
#   code VARCHAR(50),
#   name VARCHAR(100),
#   qty INT,
#   price DECIMAL(10,2)
# );
#
# CREATE TABLE customers (
#   id INT AUTO_INCREMENT PRIMARY KEY,
#   name VARCHAR(100),
#   phone VARCHAR(20),
#   email VARCHAR(100)
# );
#
# CREATE TABLE orders (
#   id INT AUTO_INCREMENT PRIMARY KEY,
#   code VARCHAR(50),
#   customer_id INT,
#   order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#   total DECIMAL(10,2),
#   FOREIGN KEY (customer_id) REFERENCES customers(id)
# );
#
# CREATE TABLE order_items (
#   id INT AUTO_INCREMENT PRIMARY KEY,
#   order_id INT,
#   product_id INT,
#   quantity INT,
#   price DECIMAL(10,2),
#   FOREIGN KEY (order_id) REFERENCES orders(id),
#   FOREIGN KEY (product_id) REFERENCES products(id)
# );
#
# CREATE TABLE users (
#  id INT AUTO_INCREMENT PRIMARY KEY,
#  username VARCHAR(80) UNIQUE NOT NULL,
#  password_hash VARCHAR(255) NOT NULL
# );

# Product CRUD routes
@app.route('/')
def index():
    return send_file('index.html')

@app.route('/add_product', methods=['POST'])
@login_required
def add_product():
    code = request.form['code']
    name = request.form['name']
    qty = request.form['qty']
    price = request.form['price']
    category = request.form['category']
    
    image_filename = None
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            image_filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (code, name, qty, price, image_url, category) VALUES (%s, %s, %s, %s, %s, %s)", (code, name, qty, price, image_filename, category))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Product added successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/edit_product/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form['name']
        code = request.form['code']
        category = request.form['category']
        qty = request.form['qty']
        price = request.form['price']
        
        image_filename = request.form.get('current_image') # Keep old image by default

        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                image_filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
            elif file and not allowed_file(file.filename):
                flash('Invalid file type. Allowed types are png, jpg, jpeg, gif.', 'danger')
                cursor.close()
                conn.close()
                return redirect(request.url)


        cursor.execute("""
            UPDATE products 
            SET name = %s, code = %s, category = %s, qty = %s, price = %s, image_url = %s 
            WHERE id = %s
        """, (name, code, category, qty, price, image_filename, id))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('index'))

    # GET request
    cursor.execute("SELECT * FROM products WHERE id = %s", (id,))
    product = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('edit_product.html', product=product)

@app.route('/delete_product/<int:id>')
@login_required
def delete_product(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # Check if product is referenced in order_items
    cursor.execute("SELECT id FROM order_items WHERE product_id = %s", (id,))
    order_item = cursor.fetchone()
    if order_item:
        flash('Cannot delete product because it is referenced in existing orders.', 'danger')
        cursor.close()
        conn.close()
        return redirect(url_for('index'))
    # If not referenced, proceed with deletion
    cursor.close()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Product deleted!', 'danger')
    return redirect(url_for('index'))

# Customer info routes
@app.route('/customers')
@login_required
def customers():
    search_query = request.args.get('search', '')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if search_query:
        # Search for customers by name or phone using LIKE
        cursor.execute("SELECT * FROM customers WHERE full_name LIKE %s OR phone LIKE %s", 
                      (f'%{search_query}%', f'%{search_query}%'))
    else:
        # Get all customers if no search query
        cursor.execute("SELECT * FROM customers")
    
    customers = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('customers.html', customers=customers, search_query=search_query)

@app.route('/customers/search')
@login_required
def customer_search():
    query = request.args.get('query', '')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if query:
        # Search for customers by name or phone using LIKE
        cursor.execute("SELECT * FROM customers WHERE full_name LIKE %s OR phone LIKE %s", 
                      (f'%{query}%', f'%{query}%'))
    else:
        # Get all customers if no search query
        cursor.execute("SELECT * FROM customers")
    
    customers = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('customers.html', customers=customers, search_query=query)

@app.route('/add_customer', methods=['POST'])
@login_required
def add_customer():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        full_name = request.form['full_name']
        code = request.form['code']
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']
        gender = request.form.get('gender')
        cursor.execute("INSERT INTO customers (full_name, code, phone, email, address, gender) VALUES (%s, %s, %s, %s, %s, %s)",
                       (full_name, code, phone, email, address, gender))
        conn.commit()
        flash('Customer added!', 'success')
    except mysql.connector.Error as err:
        flash(f"Error: {err.msg}", 'danger')
    
    cursor.close()
    conn.close()
    return redirect(url_for('customers'))

@app.route('/delete_customer/<int:id>')
@login_required
def delete_customer(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Check if the customer has any orders
    cursor.execute("SELECT id FROM orders WHERE customer_id = %s", (id,))
    order = cursor.fetchone()

    if order:
        flash('Cannot delete customer because they have existing orders.', 'danger')
        cursor.close()
        conn.close()
        return redirect(url_for('customers'))

    # If no orders, proceed with deletion
    cursor.execute("DELETE FROM customers WHERE id=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Customer deleted successfully!', 'success')
    return redirect(url_for('customers'))

@app.route('/edit_customer/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_customer(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        try:
            full_name = request.form['full_name']
            code = request.form['code']
            phone = request.form['phone']
            email = request.form['email']
            address = request.form['address']
            gender = request.form.get('gender')
            cursor.execute("UPDATE customers SET full_name=%s, code=%s, phone=%s, email=%s, address=%s, gender=%s WHERE id=%s",
                           (full_name, code, phone, email, address, gender, id))
            conn.commit()
            flash('Customer updated successfully!', 'success')
        except mysql.connector.Error as err:
            flash(f"Error: {err.msg}", 'danger')

        cursor.close()
        conn.close()
        return redirect(url_for('customers'))

    # GET request
    cursor.execute("SELECT * FROM customers WHERE id = %s", (id,))
    customer = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('edit_customer.html', customer=customer)

# Staff Management Routes
@app.route('/staff')
@login_required
def staff():
    search_query = request.args.get('search', '')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if search_query:
        # Search for staff by name or position using LIKE
        cursor.execute("SELECT * FROM staff WHERE full_name LIKE %s OR position LIKE %s ORDER BY full_name", 
                      (f'%{search_query}%', f'%{search_query}%'))
    else:
        # Get all staff if no search query
        cursor.execute("SELECT * FROM staff ORDER BY full_name")
    
    staff_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('staff.html', staff_list=staff_list, search_query=search_query)

@app.route('/staff/search')
@login_required
def staff_search():
    query = request.args.get('query', '')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if query:
        # Search for staff by name or position using LIKE
        cursor.execute("SELECT * FROM staff WHERE full_name LIKE %s OR position LIKE %s ORDER BY full_name", 
                      (f'%{query}%', f'%{query}%'))
    else:
        # Get all staff if no search query
        cursor.execute("SELECT * FROM staff ORDER BY full_name")
    
    staff_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('staff.html', staff_list=staff_list, search_query=query)

@app.route('/add_staff', methods=['POST'])
@login_required
def add_staff():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        full_name = request.form['full_name']
        position = request.form['position']
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']
        
        profile_picture_filename = None
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and allowed_file(file.filename):
                profile_picture_filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], profile_picture_filename))

        # Generate a unique staff code
        staff_code = f"STF-{secrets.token_hex(4).upper()}"
        gender = request.form.get('gender')

        cursor.execute("""
            INSERT INTO staff (full_name, position, phone, email, address, profile_picture, code, gender) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (full_name, position, phone, email, address, profile_picture_filename, staff_code, gender))
        conn.commit()
        flash('Staff member added successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f"Error: {err.msg}", 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('staff'))

@app.route('/edit_staff/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_staff(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        try:
            full_name = request.form['full_name']
            position = request.form['position']
            phone = request.form['phone']
            email = request.form['email']
            address = request.form['address']
            gender = request.form.get('gender')
            
            profile_picture_filename = request.form.get('current_profile_picture')

            if 'profile_picture' in request.files:
                file = request.files['profile_picture']
                if file and allowed_file(file.filename):
                    # Delete old picture if a new one is uploaded
                    if profile_picture_filename:
                        try:
                            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], profile_picture_filename))
                        except FileNotFoundError:
                            pass # Ignore if file doesn't exist
                    
                    profile_picture_filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], profile_picture_filename))

            cursor.execute("""
                UPDATE staff SET full_name=%s, position=%s, phone=%s, email=%s, address=%s, profile_picture=%s, gender=%s 
                WHERE id=%s
            """, (full_name, position, phone, email, address, profile_picture_filename, gender, id))
            conn.commit()
            flash('Staff member updated successfully!', 'success')
        except mysql.connector.Error as err:
            flash(f"Error: {err.msg}", 'danger')
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('staff'))
    
    # GET request
    cursor.execute("SELECT * FROM staff WHERE id = %s", (id,))
    staff_member = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('edit_staff.html', staff_member=staff_member)

@app.route('/delete_staff/<int:id>')
@login_required
def delete_staff(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) # Use dictionary cursor to get filename
    try:
        # First, get the filename of the profile picture to delete it from the server
        cursor.execute("SELECT profile_picture FROM staff WHERE id = %s", (id,))
        staff_member = cursor.fetchone()
        if staff_member and staff_member['profile_picture']:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], staff_member['profile_picture']))
            except FileNotFoundError:
                pass # File was already deleted or never existed

        # Now, delete the staff member record from the database
        cursor.execute("DELETE FROM staff WHERE id=%s", (id,))
        conn.commit()
        flash('Staff member deleted successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f"Error: {err.msg}", 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('staff'))

# Order system routes
@app.route('/orders')
@login_required
def orders():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get filter/search parameters
    customer_id = request.args.get('customer_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    search = request.args.get('search')

    # Build SQL query dynamically
    sql = """
        SELECT 
            o.id, o.code, o.order_date, o.total, c.full_name as customer,
            GROUP_CONCAT(CONCAT(p.name, ' (', oi.quantity, ')') SEPARATOR '<br/>') as items_summary
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        LEFT JOIN order_items oi ON o.id = oi.order_id
        LEFT JOIN products p ON oi.product_id = p.id
    """
    filters = []
    params = []
    if customer_id:
        filters.append("o.customer_id = %s")
        params.append(customer_id)
    if start_date:
        filters.append("DATE(o.order_date) >= %s")
        params.append(start_date)
    if end_date:
        filters.append("DATE(o.order_date) <= %s")
        params.append(end_date)
    if search:
        filters.append("(o.code LIKE %s OR c.full_name LIKE %s OR p.name LIKE %s)")
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    if filters:
        sql += " WHERE " + " AND ".join(filters)
    sql += " GROUP BY o.id, o.code, o.order_date, o.total, c.full_name ORDER BY o.order_date DESC"

    cursor.execute(sql, tuple(params))
    orders = cursor.fetchall()

    # Fetch customers and products for the new order form and filter dropdown
    cursor.execute("SELECT id, full_name FROM customers")
    customers = cursor.fetchall()
    cursor.execute("SELECT id, name, price FROM products ORDER BY name")
    products = cursor.fetchall()

    # Fetch all order items and group by order_id
    cursor.execute("""
        SELECT oi.*, p.name as product_name
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
    """)
    order_items_raw = cursor.fetchall()
    order_items = {}
    for item in order_items_raw:
        order_id = item['order_id']
        if order_id not in order_items:
            order_items[order_id] = []
        order_items[order_id].append(item)

    cursor.close()
    conn.close()
    return render_template('orders.html', orders=orders, customers=customers, products=products, order_items=order_items,
                           filter_customer_id=customer_id, filter_start_date=start_date, filter_end_date=end_date, filter_search=search)

@app.route('/orders/search')
@login_required
def order_search():
    query = request.args.get('query', '')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Build SQL query for search
    sql = """
        SELECT 
            o.id, o.code, o.order_date, o.total, c.full_name as customer,
            GROUP_CONCAT(CONCAT(p.name, ' (', oi.quantity, ')') SEPARATOR '<br/>') as items_summary
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        LEFT JOIN order_items oi ON o.id = oi.order_id
        LEFT JOIN products p ON oi.product_id = p.id
    """
    
    if query:
        sql += " WHERE (o.code LIKE %s OR c.full_name LIKE %s)"
        sql += " GROUP BY o.id, o.code, o.order_date, o.total, c.full_name ORDER BY o.order_date DESC"
        cursor.execute(sql, (f'%{query}%', f'%{query}%'))
    else:
        sql += " GROUP BY o.id, o.code, o.order_date, o.total, c.full_name ORDER BY o.order_date DESC"
        cursor.execute(sql)
    
    orders = cursor.fetchall()

    # Fetch customers and products for the new order form and filter dropdown
    cursor.execute("SELECT id, full_name FROM customers")
    customers = cursor.fetchall()
    cursor.execute("SELECT id, name, price FROM products ORDER BY name")
    products = cursor.fetchall()

    # Fetch all order items and group by order_id
    cursor.execute("""
        SELECT oi.*, p.name as product_name
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
    """)
    order_items_raw = cursor.fetchall()
    order_items = {}
    for item in order_items_raw:
        order_id = item['order_id']
        if order_id not in order_items:
            order_items[order_id] = []
        order_items[order_id].append(item)

    cursor.close()
    conn.close()
    return render_template('orders.html', orders=orders, customers=customers, products=products, order_items=order_items,
                           filter_search=query)

@app.route('/add_order', methods=['POST'])
@login_required
def add_order():
    customer_id = request.form['customer_id']
    product_ids = request.form.getlist('product_ids[]')
    quantities = request.form.getlist('quantities[]')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Calculate total order amount
        total = 0
        order_items = []
        
        # Get product prices and calculate subtotals
        for product_id, qty in zip(product_ids, quantities):
            cursor.execute("SELECT price FROM products WHERE id=%s", (product_id,))
            product = cursor.fetchone()
            qty = int(qty)
            subtotal = qty * product['price']
            total += subtotal
            order_items.append({
                'product_id': product_id,
                'quantity': qty,
                'price': product['price'],
                'subtotal': subtotal
            })
        
        # Generate order code
        order_code = f"ORD-{secrets.token_hex(4).upper()}"
        
        # Create the order
        cursor.execute("""
            INSERT INTO orders (customer_id, code, total) 
            VALUES (%s, %s, %s)
        """, (customer_id, order_code, total))
        
        order_id = cursor.lastrowid
        
        # Create order items
        for item in order_items:
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, price, subtotal) 
                VALUES (%s, %s, %s, %s, %s)
            """, (order_id, item['product_id'], item['quantity'], item['price'], item['subtotal']))
        
        conn.commit()
        flash('Order placed successfully!', 'success')
    except mysql.connector.Error as err:
        conn.rollback()
        flash(f'Error placing order: {err}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('orders'))

@app.route('/edit_order/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_order(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        customer_id = request.form['customer_id']
        product_ids = request.form.getlist('product_ids[]')
        quantities = request.form.getlist('quantities[]')
        
        try:
            # Calculate total order amount
            total = 0
            order_items = []
            
            # Get product prices and calculate subtotals
            for product_id, qty in zip(product_ids, quantities):
                cursor.execute("SELECT price FROM products WHERE id=%s", (product_id,))
                product = cursor.fetchone()
                qty = int(qty)
                subtotal = qty * product['price']
                total += subtotal
                order_items.append({
                    'product_id': product_id,
                    'quantity': qty,
                    'price': product['price'],
                    'subtotal': subtotal
                })
            
            # Update the order
            cursor.execute("""
                UPDATE orders 
                SET customer_id=%s, total=%s 
                WHERE id=%s
            """, (customer_id, total, id))
            
            # Delete existing order items
            cursor.execute("DELETE FROM order_items WHERE order_id=%s", (id,))
            
            # Create new order items
            for item in order_items:
                cursor.execute("""
                    INSERT INTO order_items (order_id, product_id, quantity, price, subtotal) 
                    VALUES (%s, %s, %s, %s, %s)
                """, (id, item['product_id'], item['quantity'], item['price'], item['subtotal']))
            
            conn.commit()
            flash('Order updated successfully!', 'success')
            return redirect(url_for('orders'))
            
        except mysql.connector.Error as err:
            conn.rollback()
            flash(f'Error updating order: {err}', 'danger')
            return redirect(url_for('edit_order', id=id))

    # GET request
    # Get order details
    cursor.execute("""
        SELECT o.*, c.full_name as customer_name 
        FROM orders o 
        JOIN customers c ON o.customer_id = c.id 
        WHERE o.id = %s
    """, (id,))
    order = cursor.fetchone()
    
    if not order:
        cursor.close()
        conn.close()
        flash('Order not found!', 'danger')
        return redirect(url_for('orders'))
    
    # Get order items
    cursor.execute("""
        SELECT oi.*, p.name as product_name 
        FROM order_items oi 
        JOIN products p ON oi.product_id = p.id 
        WHERE oi.order_id = %s
    """, (id,))
    order_items = cursor.fetchall()
    
    # Get customers and products for dropdowns
    cursor.execute("SELECT id, full_name FROM customers")
    customers = cursor.fetchall()
    
    cursor.execute("SELECT id, name, price FROM products ORDER BY name")
    products = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('edit_order.html', 
                         order=order, 
                         order_items=order_items,
                         customers=customers, 
                         products=products)

@app.route('/delete_order/<int:id>')
@login_required
def delete_order(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Delete order items first (should cascade, but let's be explicit)
        cursor.execute("DELETE FROM order_items WHERE order_id=%s", (id,))
        cursor.execute("DELETE FROM orders WHERE id=%s", (id,))
        conn.commit()
        flash('Order deleted successfully!', 'success')
    except mysql.connector.Error as err:
        conn.rollback()
        flash(f'Error deleting order: {err}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('orders'))

# Export orders as CSV
@app.route('/export_orders')
@login_required
def export_orders():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT o.code, o.order_date, o.total, c.full_name as customer_name
        FROM orders o
        LEFT JOIN customers c ON o.customer_id = c.id
        ORDER BY o.order_date DESC
    """)
    
    orders = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Order Code', 'Order Date', 'Customer Name', 'Total'])
    
    for order in orders:
        writer.writerow([
            order['code'],
            order['order_date'].strftime('%Y-%m-%d %H:%M:%S') if order['order_date'] else '',
            order['customer_name'] or 'Unknown',
            f"${order['total']:.2f}" if order['total'] else '$0.00'
        ])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'orders_export_{time.strftime("%Y%m%d_%H%M%S")}.csv'
    )

# API Endpoints for standalone index.html
@app.route('/api/products', methods=['GET'])
def api_get_products():
    search_query = request.args.get('search', '')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        if search_query:
            cursor.execute("SELECT * FROM products WHERE name LIKE %s", (f'%{search_query}%',))
        else:
            cursor.execute("SELECT * FROM products")
        
        products = cursor.fetchall()
        return jsonify({'success': True, 'products': products})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/products', methods=['POST'])
def api_add_product():
    try:
        code = request.form['code']
        name = request.form['name']
        category = request.form['category']
        qty = int(request.form['qty'])
        price = float(request.form['price'])
        
        # Handle file upload
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to prevent filename conflicts
                name_without_ext = os.path.splitext(filename)[0]
                ext = os.path.splitext(filename)[1]
                filename = f"{name_without_ext}_{int(time.time())}{ext}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_url = filename
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO products (code, name, category, qty, price, image_url) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (code, name, category, qty, price, image_url))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Product added successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/products/<int:id>', methods=['DELETE'])
def api_delete_product(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get product info to delete image file
        cursor.execute("SELECT image_url FROM products WHERE id = %s", (id,))
        product = cursor.fetchone()
        
        if not product:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Product not found'}), 404
        
        # Delete the product
        cursor.execute("DELETE FROM products WHERE id = %s", (id,))
        conn.commit()
        
        # Delete image file if it exists
        if product['image_url']:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], product['image_url'])
            if os.path.exists(image_path):
                os.remove(image_path)
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Product deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Serve the standalone index.html file
@app.route('/index.html')
def serve_index():
    return send_file('index.html')

if __name__ == '__main__':
    app.run(debug=True)
