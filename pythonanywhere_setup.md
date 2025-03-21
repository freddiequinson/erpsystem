# PythonAnywhere Deployment Guide

This guide provides step-by-step instructions for deploying this application on PythonAnywhere.

## Initial Setup

1. Create a PythonAnywhere account at [pythonanywhere.com](https://www.pythonanywhere.com)
2. Open a Bash console in PythonAnywhere

## Clone the Repository

```bash
git clone https://github.com/yourusername/odoo-clone.git
cd odoo-clone
```

## Set Up Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configure Web App

1. Go to the Web tab in PythonAnywhere
2. Click "Add a new web app"
3. Choose "Manual configuration" (not Flask)
4. Select Python 3.8 or higher

## Configure WSGI File

Edit the WSGI file (there will be a link to it in the Web tab) and replace its contents with:

```python
import sys
import os

# Add the app directory to the Python path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

# Import the Flask app object
from app import app as application
```

## Initialize the Database

```bash
cd ~/odoo-clone
source venv/bin/activate
python init_db.py
```

## Configure Static Files

In the Web tab, add the following static file mappings:
- URL: /static/ -> Directory: /home/yourusername/odoo-clone/static/

## Final Steps

1. Go back to the Web tab
2. Click the "Reload" button for your web app
3. Visit your site at yourusername.pythonanywhere.com

## Default Admin Login

- Username: admin
- Password: admin123

## Branch-Specific Setup

For setting up multiple branches, create separate PythonAnywhere accounts and repeat this process for each branch.
