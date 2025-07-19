# Skincare Shop Backend

A Flask-based web application for managing a skincare shop with product, customer, staff, and order management capabilities.

## Project Structure

```
skincare-backend/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── render.yaml           # Render deployment configuration
├── skincareshop.sql      # Database schema
├── setup_db.py           # Database setup script
├── templates/            # Jinja2 HTML templates
│   ├── base.html         # Base template
│   ├── index.html        # Product management page
│   ├── customers.html    # Customer management page
│   ├── staff.html        # Staff management page
│   ├── orders.html       # Order management page
│   ├── login.html        # Login page
│   ├── register.html     # Registration page
│   └── edit_*.html       # Edit forms for various entities
└── static/               # Static files (CSS, JS, images)
    └── uploads/          # Uploaded product images
```

## Features

- **Product Management**: Add, edit, delete, and search products
- **Customer Management**: Manage customer information with search functionality
- **Staff Management**: Handle staff records with profile pictures
- **Order Management**: Create and manage orders with multiple products
- **User Authentication**: Login/registration system
- **Search Functionality**: Search across all modules
- **File Upload**: Product and staff image uploads
- **Database Integration**: MySQL database with connection pooling

## Local Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Database Setup
1. Create a MySQL database
2. Run the schema: `mysql -u username -p database_name < skincareshop.sql`
3. Or use the setup script: `python setup_db.py`

### 3. Environment Configuration
Create a `.env` file with:
```
DB_HOST=localhost
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=skincare_shop
SECRET_KEY=your_secret_key
```

### 4. Run the Application
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Deployment to Render

### Prerequisites
1. GitHub account with your project repository
2. Render account (free tier available)

### Step 1: Push to GitHub
1. Initialize git repository (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```

2. Create a new repository on GitHub and push your code:
   ```bash
   git remote add origin https://github.com/yourusername/skincare-shop-backend.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy on Render
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" and select "Blueprint"
3. Connect your GitHub account and select your repository
4. Render will automatically detect the `render.yaml` file and create:
   - A web service for your Flask app
   - A MySQL database
   - All necessary environment variables

### Step 3: Database Setup
After deployment, you'll need to set up your database:
1. Go to your Render dashboard
2. Find your MySQL database service
3. Connect to it and run the SQL commands from `skincareshop.sql`

### Step 4: Access Your Application
Your application will be available at the URL provided by Render (e.g., `https://skincare-shop-backend.onrender.com`)

## API Endpoints

- `GET /` - Product management page
- `GET /customers` - Customer management page
- `GET /staff` - Staff management page
- `GET /orders` - Order management page
- `GET /login` - Login page
- `GET /register` - Registration page

## Search Functionality

All modules support search:
- **Products**: Search by product name
- **Customers**: Search by name or phone
- **Staff**: Search by name or position
- **Orders**: Search by order code or customer name

## Environment Variables

The following environment variables are automatically configured by Render:
- `DB_HOST` - MySQL database host
- `DB_NAME` - Database name
- `DB_USER` - Database username
- `DB_PASSWORD` - Database password
- `SECRET_KEY` - Flask secret key (auto-generated)

## Technologies Used

- **Backend**: Flask (Python)
- **Database**: MySQL
- **Frontend**: Bootstrap 5, Jinja2 Templates
- **File Handling**: Werkzeug
- **Authentication**: Flask Sessions
- **Deployment**: Render
- **WSGI Server**: Gunicorn 