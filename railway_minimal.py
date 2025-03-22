"""
Minimal script to initialize the database on Railway.
This script avoids using pandas to ensure deployment works.
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Print environment variables for debugging (without sensitive info)
logger.info("Environment variables:")
for key in os.environ:
    if "DATABASE_URL" in key:
        logger.info(f"  {key}: [Connection string found but not displayed for security]")
    elif "SECRET" in key.upper():
        logger.info(f"  {key}: [Secret value not displayed for security]")
    else:
        logger.info(f"  {key}: {os.environ[key]}")

# Ensure DATABASE_URL is set correctly for PostgreSQL
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    # Replace postgres:// with postgresql:// for SQLAlchemy 1.4+
    logger.info("Converting postgres:// to postgresql:// in DATABASE_URL")
    os.environ['DATABASE_URL'] = database_url.replace('postgres://', 'postgresql://', 1)
elif not database_url:
    logger.warning("WARNING: DATABASE_URL is not set!")

# Import app after environment variables are set
from app_minimal import create_app
from extensions import db
from modules.auth.models import User, Role, UserRole
from modules.inventory.models import StockLocation

def init_db():
    """Initialize the database with required tables and admin user."""
    logger.info("Initializing database...")
    
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
                shop_floor = StockLocation(name='Shop Floor', code='SF', is_active=True)
                db.session.add(shop_floor)
            
            if not StockLocation.query.filter_by(name='Customer').first():
                customer = StockLocation(name='Customer', code='CUST', is_active=True)
                db.session.add(customer)
            
            db.session.commit()
            logger.info("Admin user created successfully!")
        else:
            logger.info("Admin user already exists.")
        
        logger.info("Database initialization complete!")

if __name__ == '__main__':
    init_db()
