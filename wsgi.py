"""
WSGI configuration for PythonAnywhere and Render deployment
"""

import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the app directory to the Python path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

# Import the Flask app creation function
from app import create_app
from init_db import init_db

# Log environment variables (excluding sensitive ones)
logger.info(f"FLASK_ENV: {os.environ.get('FLASK_ENV')}")
logger.info(f"FLASK_CONFIG: {os.environ.get('FLASK_CONFIG')}")
logger.info(f"RENDER: {os.environ.get('RENDER')}")
logger.info(f"DATABASE_URL exists: {bool(os.environ.get('DATABASE_URL'))}")

# Create the Flask app with production configuration
application = create_app('production')

# Initialize the database if running on Render
if os.environ.get('RENDER') == 'true':
    try:
        logger.info("Attempting to initialize database...")
        with application.app_context():
            init_db()
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        # Continue execution even if database init fails
        # This allows the application to start and show more specific errors

# For WSGI servers that look for 'app' object
app = application
