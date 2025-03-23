"""
Script to manually initialize the database on Render.
This script creates all necessary tables and the admin user.
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set environment variable for Render
os.environ['RENDER'] = 'true'
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_CONFIG'] = 'production'

# Import after setting environment variables
from app import create_app
from extensions import db
from modules.auth.models import User, Role, UserRole
from modules.inventory.models import Category, Product, StockLocation, StockMove
from flask_migrate import upgrade

def manual_init():
    """Manually initialize the database with required tables and admin user."""
    logger.info("Starting manual database initialization...")
    
    # Create app with production config
    app = create_app('production')
    
    with app.app_context():
        # Print database connection info
        db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        db_type = db_url.split('://')[0] if '://' in db_url else 'unknown'
        logger.info(f"Database URL type: {db_type}")
        
        # Create all tables
        logger.info("Creating database tables...")
        db.create_all()
        
        # Check if admin user exists
        if User.query.filter_by(username='admin').first() is None:
            logger.info("Creating admin user...")
            # Create admin user
            admin_user = User(
                username='admin',
                email='admin@example.com',
                first_name='Admin',
                last_name='User',
                is_active=True
            )
            admin_user.set_password('admin123')
            
            # Create admin role if it doesn't exist
            admin_role = Role.query.filter_by(name='admin').first()
            if not admin_role:
                admin_role = Role(name='admin', description='Administrator')
                db.session.add(admin_role)
            
            db.session.add(admin_user)
            db.session.commit()
            
            # Assign admin role to admin user
            user_role = UserRole(user_id=admin_user.id, role_id=admin_role.id)
            db.session.add(user_role)
            
            # Create default stock locations
            if not StockLocation.query.filter_by(name='Shop Floor').first():
                shop_floor = StockLocation(name='Shop Floor', code='SF', location_type='internal')
                db.session.add(shop_floor)
            
            if not StockLocation.query.filter_by(name='Customer').first():
                customer = StockLocation(name='Customer', code='CUST', location_type='customer')
                db.session.add(customer)
            
            db.session.commit()
            logger.info("Admin user created successfully!")
        else:
            logger.info("Admin user already exists.")
        
        logger.info("Database initialization complete!")

if __name__ == '__main__':
    manual_init()
