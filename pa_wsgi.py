"""
WSGI configuration for PythonAnywhere deployment
"""

import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# IMPORTANT: Replace 'yourusername' with your actual PythonAnywhere username
PYTHONANYWHERE_USERNAME = 'yourusername'

# Add the app directory to the Python path
path = '/home/' + PYTHONANYWHERE_USERNAME + '/erpsystem'
if path not in sys.path:
    sys.path.append(path)

# Import the Flask app creation function
from app import create_app
from extensions import db
from init_db import init_db

# Create the Flask app with production configuration
application = create_app('production')

# For WSGI servers that look for 'application' object
app = application
