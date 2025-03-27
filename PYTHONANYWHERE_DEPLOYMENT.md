# PythonAnywhere Deployment Guide for ERP System

This guide will walk you through deploying your ERP system with POS functionality on PythonAnywhere.

## Step 1: Create a PythonAnywhere Account

1. Go to [PythonAnywhere.com](https://www.pythonanywhere.com/) and sign up for an account
   - The free tier is sufficient for testing, but for production use, consider a paid plan (starting at $5/month)
   - Paid plans provide more resources and allow for custom domains

## Step 2: Set Up Your Web App

1. After logging in, click on the **Web** tab in the top navigation
2. Click on **Add a new web app**
3. Choose your domain name (it will be yourusername.pythonanywhere.com)
4. Select **Flask** as your framework
5. Choose **Python 3.9** or newer
6. For the path, use the default for now

## Step 3: Set Up Your Code

1. Go to the **Consoles** tab
2. Start a new **Bash console**
3. Clone your repository:
   ```bash
   git clone https://github.com/yourusername/erpsystem.git
   ```
4. Navigate to your project directory:
   ```bash
   cd erpsystem
   ```
5. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
6. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Step 4: Configure Your Web App

1. Go back to the **Web** tab
2. Click on your web app
3. Scroll to the **Code** section
4. Update the **Source code** path to `/home/yourusername/erpsystem`
5. Update the **Working directory** to `/home/yourusername/erpsystem`
6. Update the **WSGI configuration file** to point to your pa_wsgi.py file:
   - Click on the WSGI configuration file link
   - Replace the contents with the contents of your pa_wsgi.py file
   - Make sure to update `PYTHONANYWHERE_USERNAME` with your actual username
   - Save the file

## Step 5: Set Up Your Database

1. Go to the **Databases** tab
2. Initialize your PostgreSQL database
   - Note: On the free tier, you'll need to use MySQL instead of PostgreSQL
   - For paid plans, you can use PostgreSQL
3. Note your database connection details:
   - Database name
   - Username
   - Password
   - Host

## Step 6: Set Environment Variables

1. Go back to the **Web** tab
2. Scroll to the **Environment variables** section
3. Add the following environment variables:
   - `FLASK_ENV`: production
   - `FLASK_CONFIG`: production
   - `SECRET_KEY`: [generate a secure random string]
   - `JWT_SECRET_KEY`: [generate a secure random string]
   - `DATABASE_URL`: [your database connection string]
     - Format: `postgresql://username:password@host:port/database_name`
     - For MySQL: `mysql://username:password@host:port/database_name`

## Step 7: Initialize Your Database

1. Go back to the **Consoles** tab
2. Start a new **Bash console** or use the existing one
3. Navigate to your project directory:
   ```bash
   cd erpsystem
   ```
4. Activate your virtual environment:
   ```bash
   source venv/bin/activate
   ```
5. Initialize your database:
   ```bash
   python init_db.py
   ```

## Step 8: Reload Your Web App

1. Go back to the **Web** tab
2. Click the **Reload** button for your web app

## Step 9: Access Your ERP System

1. Your ERP system should now be accessible at yourusername.pythonanywhere.com
2. Log in with the default admin credentials:
   - Username: admin
   - Password: admin123

## Troubleshooting

If you encounter any issues:

1. Check the **Error log** in the **Web** tab
2. Make sure all environment variables are set correctly
3. Ensure the database is properly initialized
4. Check that all required packages are installed

## Features Available in Your ERP System

Your ERP system includes the following features:

1. **Point of Sale (POS) System**:
   - Modern, user-friendly POS interface
   - Stock locations (Shop Floor and Customers)
   - Cash register and payment methods (Cash, Card, Mobile Money)
   - Inventory validation
   - Automatic stock movements
   - All monetary values in Ghanaian Cedis (₵)

2. **Inventory Management**:
   - Product management
   - Stock tracking
   - Inventory adjustments

3. **Sales Management**:
   - Customer management
   - Sales orders
   - Invoicing
   - Payment tracking

4. **Purchase Management**:
   - Supplier management
   - Purchase orders
   - Receipts
   - Invoicing

5. **Employee Management**:
   - Department and job position management
   - Employee records
   - Attendance tracking
   - Leave management

## Maintenance and Updates

To update your application:

1. Pull the latest changes from your repository
2. Install any new dependencies
3. Apply any database migrations
4. Reload your web app

For regular maintenance, consider:
- Backing up your database regularly
- Monitoring your application's performance
- Updating dependencies for security patches
