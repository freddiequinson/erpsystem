"""
WSGI configuration for PythonAnywhere deployment
"""

import sys
import os

# Add the app directory to the Python path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

# Import the Flask app object
from app import app as application

# PythonAnywhere looks for an 'application' object by default
