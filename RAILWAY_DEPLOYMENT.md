# Railway Deployment Guide for ERP System

This guide explains how to deploy and manage your ERP System on Railway.app.

## Prerequisites

- A Railway account (sign up at [railway.app](https://railway.app))
- Your ERP System code pushed to GitHub

## Deployment Steps

### 1. Create a New Project on Railway

1. Log in to your Railway account
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Connect your GitHub account if not already connected
5. Select your ERP System repository

### 2. Add a PostgreSQL Database

1. In your project dashboard, click "New"
2. Select "Database" → "PostgreSQL"
3. Wait for the database to be provisioned

### 3. Connect Your App to the Database

1. Click on your PostgreSQL service
2. Go to the "Connect" tab
3. Copy the "Postgres Connection URL"
4. Go to your web service
5. Click on "Variables"
6. Add a new variable:
   - Name: `DATABASE_URL`
   - Value: Paste the PostgreSQL connection URL

### 4. Set Up Additional Environment Variables

Add these environment variables in the "Variables" section of your web service:
- `FLASK_ENV`: production
- `FLASK_CONFIG`: production
- `SECRET_KEY`: [generate a secure random string]
- `JWT_SECRET_KEY`: [generate another secure random string]

### 5. Access Your Application

1. Once deployed, click on the "Settings" tab
2. Under "Domains", you'll find your application URL
3. Click on the URL to access your application

## Initial Login

Use these default credentials to log in:
- Admin: username `admin`, password `admin123`
- Manager: username `manager`, password `manager123`
- Cashier: username `cashier`, password `cashier123`

**Important**: Change these passwords immediately after your first login!

## Features Available in the Deployed Application

1. **Point of Sale (POS) System**
   - Terminal interface for sales
   - Checkout functionality
   - Inventory validation
   - Stock movements

2. **Inventory Management**
   - Product tracking
   - Stock movement validation
   - Warehouse management

3. **User Management**
   - Role-based access control
   - Branch-specific product views

## Troubleshooting

### Database Issues

If you encounter database issues:
1. Check the Railway logs in the "Deployments" tab
2. Verify that the DATABASE_URL environment variable is correct
3. You may need to manually run `python init_db.py` if the database isn't initialized

### Missing Functionality

If certain features are missing:
1. Check that all required environment variables are set
2. Verify that the database was properly initialized
3. Check the logs for any errors during deployment

### Performance Issues

If the application is slow:
1. Railway's free tier has limited resources
2. Consider upgrading to a paid plan for better performance
3. Optimize database queries and reduce unnecessary operations

## Maintenance

### Updating Your Application

1. Push changes to your GitHub repository
2. Railway will automatically detect changes and redeploy

### Database Backups

1. Railway provides automatic backups for PostgreSQL databases
2. You can also manually export data using the export functionality in your application

### Monitoring

1. Use Railway's built-in monitoring tools to track application performance
2. Check logs regularly for any errors or issues

## Support

If you encounter any issues with your deployment, please:
1. Check the Railway documentation: [docs.railway.app](https://docs.railway.app)
2. Review application logs for specific error messages
3. Contact Railway support for platform-specific issues
