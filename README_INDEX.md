# Standalone Index.html

This `index.html` file has been moved out of the templates directory and converted to a standalone HTML file that can be deployed separately on GitHub Pages or any static hosting service.

## Features

- **Static HTML**: No server-side rendering required
- **JavaScript API Integration**: Communicates with the Flask backend via REST API
- **Product Management**: View, add, edit, and delete products
- **Search Functionality**: Real-time search through products
- **Responsive Design**: Works on desktop and mobile devices
- **Bootstrap 5**: Modern, clean UI

## How It Works

The standalone `index.html` uses JavaScript to:

1. **Load Products**: Fetches product data from `/api/products` endpoint
2. **Search Products**: Sends search queries to `/api/products?search=query`
3. **Add Products**: Submits form data to `/api/products` (POST)
4. **Delete Products**: Sends DELETE requests to `/api/products/{id}`

## API Endpoints Required

The Flask backend must provide these API endpoints:

- `GET /api/products` - List all products (supports `?search=query` parameter)
- `POST /api/products` - Add a new product (multipart form data)
- `DELETE /api/products/{id}` - Delete a product by ID

## Deployment Options

### Option 1: GitHub Pages
1. Create a new repository on GitHub
2. Upload the `index.html` file to the repository
3. Enable GitHub Pages in repository settings
4. Set the source to "Deploy from a branch" and select main branch

### Option 2: Netlify
1. Drag and drop the `index.html` file to Netlify
2. Your site will be live instantly

### Option 3: Vercel
1. Create a new project on Vercel
2. Upload the `index.html` file
3. Deploy automatically

## Backend Requirements

To use this standalone frontend, you need:

1. **Flask Backend**: Running with the API endpoints mentioned above
2. **Database**: MySQL database with products table
3. **File Upload**: Support for image uploads to `static/uploads/`
4. **CORS**: If deploying frontend and backend on different domains

## Customization

You can customize the standalone `index.html` by:

1. **Styling**: Modify the inline CSS or link to external stylesheets
2. **API Endpoints**: Change the API URLs to point to your backend
3. **Features**: Add or remove functionality as needed
4. **Branding**: Update colors, logos, and text

## File Structure

```
skincare-backend/
├── index.html          # Standalone frontend
├── app.py              # Flask backend with API endpoints
├── static/
│   ├── style.css       # Main styles
│   ├── pink_theme.css  # Theme styles
│   └── uploads/        # Product images
└── templates/          # Other Jinja2 templates
```

## Notes

- The standalone `index.html` is self-contained and doesn't require Jinja2 templating
- All interactions are handled via JavaScript and API calls
- The file includes inline CSS for immediate styling
- Bootstrap 5 is loaded from CDN for responsive design
- Product images are served from the Flask backend's static/uploads directory 