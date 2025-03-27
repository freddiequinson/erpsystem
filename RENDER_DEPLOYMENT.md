# Deploying Your ERP System on Render

This guide will walk you through deploying your ERP system with POS functionality on Render.

## Why Switch to Render?

Render is a great alternative to Railway for Python applications, especially those using data science libraries like pandas. Render has better support for these dependencies and provides a more straightforward deployment process.

## Prerequisites

- A Render account (sign up at [render.com](https://render.com))
- Your code pushed to a GitHub repository

## Deployment Steps

### 1. Sign Up for Render

1. Go to [render.com](https://render.com)
2. Sign up using your GitHub account or email

### 2. Create a New Web Service

1. From your Render dashboard, click "New +" and select "Web Service"
2. Connect your GitHub repository
3. Select the repository containing your ERP system

### 3. Configure Your Web Service

Use these settings:
- **Name**: erpsystem (or any name you prefer)
- **Environment**: Python
- **Region**: Choose the closest to your users
- **Branch**: main (or your preferred branch)
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn wsgi:app --bind 0.0.0.0:$PORT`

### 4. Set Up Environment Variables

Add these environment variables:
- `FLASK_ENV`: production
- `FLASK_CONFIG`: production
- `RENDER`: true
- `SECRET_KEY`: (generate a secure random string)
- `JWT_SECRET_KEY`: (generate another secure random string)

### 5. Create a PostgreSQL Database

1. From your Render dashboard, click "New +" and select "PostgreSQL"
2. Name it "erpsystem-db" (or any name you prefer)
3. Choose the free plan for testing
4. Note the Internal Database URL

### 6. Link Your Database

1. After your database is created, click on it to view its details
2. Look for "Internal Database URL" and copy it
3. Go back to your web service by clicking on its name in the dashboard
4. Click on "Environment" in the left sidebar
5. Add a new environment variable:
   - **Key**: DATABASE_URL
   - **Value**: (paste the Internal Database URL you copied)
6. Click "Save Changes"

### 7. Deploy Your Application

1. Click "Create Web Service" to start the deployment process
2. Wait for your application to build and deploy (this may take a few minutes)
3. The database will be automatically initialized during startup thanks to the code in wsgi.py

## Testing Your Deployment

Once deployed, your ERP system with POS functionality should be accessible at the URL provided by Render (something like `https://erpsystem.onrender.com`).

Test the following features:
1. Login with default credentials (admin/admin123)
2. POS terminal interface
3. Inventory management
4. Order creation and checkout

## POS System Features

Your deployed POS system includes:
1. A modern, user-friendly terminal interface
2. Stock locations (Shop Floor and Customers) for inventory tracking
3. Cash register and payment methods (Cash, Card, Mobile Money)
4. All monetary values displayed in Ghanaian Cedis (₵)
5. Stock validation to prevent selling products with insufficient inventory
6. Automatic stock movements when products are sold

## Troubleshooting

If you encounter issues:
1. Check the logs in your Render dashboard
2. Verify that all environment variables are set correctly
3. Ensure the database connection string is properly formatted

## Maintenance

Render automatically deploys new changes when you push to your GitHub repository. To update your application, simply push your changes and Render will handle the deployment.
