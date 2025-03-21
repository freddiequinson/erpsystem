# PythonAnywhere Deployment Guide for ERP System

This guide will walk you through deploying your ERP System on PythonAnywhere, making it accessible online.

## Prerequisites

1. A PythonAnywhere account (Free tier works for testing, but you may want a paid account for production)
2. Your ERP System code pushed to GitHub (which you've already done)

## Step 1: Sign Up/Login to PythonAnywhere

1. Go to [PythonAnywhere](https://www.pythonanywhere.com/)
2. Sign up for a new account or log in to your existing account

## Step 2: Create a New Web App

1. Once logged in, go to the Dashboard
2. Click on the "Web" tab
3. Click "Add a new web app"
4. Choose your domain name (e.g., yourusername.pythonanywhere.com)
5. Select "Manual configuration" (not Flask)
6. Choose Python 3.9 or higher

## Step 3: Clone Your Repository

1. Go to the "Consoles" tab
2. Start a new Bash console
3. Clone your repository using:
   ```bash
   git clone https://github.com/freddiequinson/erpsystem.git
   ```
4. Navigate to your project directory:
   ```bash
   cd erpsystem
   ```

## Step 4: Set Up a Virtual Environment

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
2. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```
3. Install your project dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   
   Note: If you don't have a requirements.txt file, create one with:
   ```bash
   pip freeze > requirements.txt
   ```

## Step 5: Configure the WSGI File

1. Go back to the "Web" tab
2. Click on the WSGI configuration file link (e.g., `/var/www/yourusername_pythonanywhere_com_wsgi.py`)
3. Replace the contents with the following (adjust paths as needed):

```python
import sys
import os

# Add your project directory to the Python path
path = '/home/yourusername/erpsystem'
if path not in sys.path:
    sys.path.append(path)

# Set environment variables
os.environ['FLASK_ENV'] = 'production'

# Import your app
from app import create_app

# Create the application with the production configuration
application = create_app('production')
```

4. Save the file

## Step 6: Configure Static Files

1. In the "Web" tab, scroll down to "Static files"
2. Add the following mappings:
   - URL: `/static/` → Directory: `/home/yourusername/erpsystem/static/`
   - URL: `/uploads/` → Directory: `/home/yourusername/erpsystem/uploads/` (if you have file uploads)

## Step 7: Configure the Virtual Environment Path

1. In the "Web" tab, scroll to "Virtualenv"
2. Enter the path to your virtual environment: `/home/yourusername/erpsystem/venv`

## Step 8: Initialize the Database

1. Go back to the "Consoles" tab
2. Start a new Bash console or use the existing one
3. Navigate to your project directory:
   ```bash
   cd erpsystem
   ```
4. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```
5. Initialize the database:
   ```bash
   python init_db.py
   ```

## Step 9: Update Configuration for Production

1. Make sure your `config.py` file has a production configuration that:
   - Uses a secure secret key
   - Disables debug mode
   - Uses the correct database path (SQLite or MySQL depending on your plan)

2. Example production configuration:
   ```python
   class ProductionConfig(Config):
       DEBUG = False
       SQLALCHEMY_DATABASE_URI = 'sqlite:///erp_system.db'  # Adjust as needed
       # For MySQL (on paid plans):
       # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://yourusername:password@yourusername.mysql.pythonanywhere-services.com/yourusername$erpsystem'
   ```

## Step 10: Reload Your Web App

1. Go back to the "Web" tab
2. Click the "Reload" button for your web app

## Step 11: Test Your Application

1. Visit your PythonAnywhere domain (e.g., yourusername.pythonanywhere.com)
2. Verify that your application is working correctly
3. Test all major functionality to ensure everything works as expected

## Troubleshooting

If your application doesn't work, check the following:

1. **Error Logs**: In the "Web" tab, check the "Error log" link
2. **File Permissions**: Ensure your files have the correct permissions
3. **Database Path**: Make sure your database path is correct and accessible
4. **Static Files**: Verify that static files are configured correctly
5. **Dependencies**: Ensure all required packages are installed in your virtual environment

## Updating Your Application

When you make changes to your code:

1. Push changes to GitHub
2. In PythonAnywhere, open a Bash console
3. Navigate to your project directory
4. Pull the latest changes:
   ```bash
   git pull
   ```
5. If you've added new dependencies, install them:
   ```bash
   pip install -r requirements.txt
   ```
6. Go to the "Web" tab and click "Reload"

## Additional Tips for Your ERP System

1. **Database Backups**: Regularly back up your database
2. **Secret Key**: Use a strong, unique secret key in production
3. **File Uploads**: Configure the upload directory properly
4. **Hard Reset**: Use your new system reset functionality with caution in production
5. **SSL**: Consider enabling HTTPS for security (available on paid plans)

## Conclusion

Your ERP System should now be successfully deployed on PythonAnywhere and accessible online. Remember to monitor your application's performance and make adjustments as needed.
