# GitHub Pages Deployment Guide

This guide will help you deploy the standalone `index.html` file to GitHub Pages.

## Step 1: Create a New GitHub Repository

1. Go to [GitHub](https://github.com) and sign in
2. Click the "+" icon in the top right and select "New repository"
3. Name your repository (e.g., `skincare-shop-frontend`)
4. Make it public (required for free GitHub Pages)
5. **Don't** initialize with README, .gitignore, or license
6. Click "Create repository"

## Step 2: Upload the index.html File

### Option A: Using GitHub Web Interface
1. In your new repository, click "uploading an existing file"
2. Drag and drop the `index.html` file from your `skincare-backend` folder
3. Add a commit message like "Add standalone index.html"
4. Click "Commit changes"

### Option B: Using Git Commands
```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/skincare-shop-frontend.git
cd skincare-shop-frontend

# Copy the index.html file
cp ../skincare-backend/index.html .

# Add and commit
git add index.html
git commit -m "Add standalone index.html"
git push origin main
```

## Step 3: Enable GitHub Pages

1. Go to your repository on GitHub
2. Click on "Settings" tab
3. Scroll down to "Pages" section (or click "Pages" in the left sidebar)
4. Under "Source", select "Deploy from a branch"
5. Choose "main" branch and "/ (root)" folder
6. Click "Save"

## Step 4: Access Your Site

Your site will be available at:
```
https://YOUR_USERNAME.github.io/skincare-shop-frontend
```

It may take a few minutes for the site to be published.

## Step 5: Configure Backend URL

If your Flask backend is deployed on a different domain, you'll need to update the API endpoints in the `index.html` file:

1. Open the `index.html` file in your repository
2. Find the JavaScript section
3. Update the API URLs to point to your backend:

```javascript
// Change from relative URLs to absolute URLs
let url = 'https://your-backend-domain.com/api/products';
```

## Step 6: Test Your Deployment

1. Visit your GitHub Pages URL
2. Test the following features:
   - Loading products
   - Searching products
   - Adding new products
   - Deleting products

## Troubleshooting

### CORS Issues
If you get CORS errors, you may need to:
1. Add CORS headers to your Flask backend
2. Or deploy both frontend and backend on the same domain

### API Connection Issues
- Check that your backend is running and accessible
- Verify the API endpoints are correct
- Check browser console for error messages

### Styling Issues
- The `index.html` includes inline CSS, so styling should work immediately
- If you want to use external CSS files, you'll need to host them separately

## Custom Domain (Optional)

To use a custom domain:
1. In repository Settings > Pages
2. Enter your custom domain
3. Add a CNAME file to your repository
4. Configure DNS with your domain provider

## Next Steps

After successful deployment:
1. Share your GitHub Pages URL
2. Consider adding more features to the frontend
3. Set up monitoring for your backend API
4. Add analytics to track usage

---

**🎉 Congratulations!** Your standalone frontend is now live on GitHub Pages! 