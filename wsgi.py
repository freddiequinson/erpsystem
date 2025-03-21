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
from extensions import db
from init_db import init_db

# Create the Flask app with production configuration
application = create_app('production')

# Initialize the database if running on Render
if os.environ.get('RENDER') == 'true':
    try:
        logger.info("Attempting to initialize database...")
        with application.app_context():
            # First, create all tables
            logger.info("Creating database tables...")
            db.create_all()
            
            # Then run the initialization script
            logger.info("Running database initialization script...")
            init_db()
            
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

# For WSGI servers that look for 'app' object
app = application
