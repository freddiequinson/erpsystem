"""
Script to initialize the database on Railway.
This script will create all necessary tables and the admin user.
"""
import os
import sys

# Handle pandas import issues
try:
    # Try to disable pandas warnings that might be causing issues
    import warnings
    warnings.filterwarnings('ignore', category=UserWarning, module='pandas')
    
    # Try specific pandas import to ensure it works
    import pandas
    print(f"Successfully imported pandas version: {pandas.__version__}")
except ImportError as e:
    print(f"Warning: Pandas import issue: {e}")
    print("Continuing without pandas as it may not be needed for core functionality...")

# Print environment variables for debugging (without sensitive info)
print("Environment variables:")
for key in os.environ:
    if "DATABASE_URL" in key:
        print(f"  {key}: [Connection string found but not displayed for security]")
    elif "SECRET" in key.upper():
        print(f"  {key}: [Secret value not displayed for security]")
    else:
        print(f"  {key}: {os.environ[key]}")

# Ensure DATABASE_URL is set correctly for PostgreSQL
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    # Replace postgres:// with postgresql:// for SQLAlchemy 1.4+
    print("Converting postgres:// to postgresql:// in DATABASE_URL")
    os.environ['DATABASE_URL'] = database_url.replace('postgres://', 'postgresql://', 1)
elif not database_url:
    print("WARNING: DATABASE_URL is not set!")

from app import create_app, db
from modules.auth.models import User, Role, UserRole
from modules.inventory.models import Category, Product, StockLocation, StockMove
from flask_migrate import upgrade

def init_db():
    """Initialize the database with required tables and admin user."""
    print("Initializing database...")
    
    # Create app with production config
    app = create_app('production')
    
    with app.app_context():
        # Print database connection info
        print(f"Database URL type: {app.config.get('SQLALCHEMY_DATABASE_URI', '').split('://')[0] if '://' in app.config.get('SQLALCHEMY_DATABASE_URI', '') else 'unknown'}")
        
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        
        # Check if admin user exists
        if User.query.filter_by(username='admin').first() is None:
            print("Creating admin user...")
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
            print("Admin user created successfully!")
        else:
            print("Admin user already exists.")
        
        print("Database initialization complete!")

if __name__ == '__main__':
    init_db()
