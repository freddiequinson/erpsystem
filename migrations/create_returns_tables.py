from app import db
from flask import Flask
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.pos.models import POSReturn, POSReturnLine, QualityCheck

def create_returns_tables():
    """Create the necessary tables for the returns management system."""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///odoo_clone.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        # Create the tables
        db.create_all()
        print("Returns management tables created successfully!")

if __name__ == "__main__":
    create_returns_tables()
