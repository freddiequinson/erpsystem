"""
WSGI configuration for PythonAnywhere and Render deployment
"""

import sys
import os

# Add the app directory to the Python path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

# Import the Flask app creation function
from app import create_app
from init_db import init_db

# Create the Flask app with production configuration
application = create_app('production')

# Initialize the database if running on Render
if os.environ.get('RENDER') == 'true':
    with application.app_context():
        init_db()

# For WSGI servers that look for 'app' object
app = application
