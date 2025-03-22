"""
Setup Database Script
This script initializes the database with all required tables and creates an admin user.
"""
from app import create_app, db
from modules.auth.models import User, Role, UserRole
from modules.pos.models import POSCashRegister
from modules.inventory.models import StockLocation
import bcrypt

def setup_database():
    print("Setting up the database...")
    
    # Create Flask app with development configuration
    app = create_app('development')
    
    with app.app_context():
        # Create all database tables
        print("Creating database tables...")
        db.create_all()
        
        # Check if admin role exists
        admin_role = Role.query.filter_by(name='Admin').first()
        if not admin_role:
            print("Creating admin role...")
            admin_role = Role(name='Admin', description='Administrator with full access')
            db.session.add(admin_role)
            db.session.commit()
        
        # Check if admin user exists
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("Creating admin user...")
            # Generate password hash
            password = 'admin123'
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Create admin user
            admin_user = User(
                username='admin',
                email='admin@example.com',
                password_hash=password_hash,
                first_name='Admin',
                last_name='User',
                is_active=True
            )
            db.session.add(admin_user)
            db.session.commit()
            
            # Assign admin role to admin user
            if not UserRole.query.filter_by(user_id=admin_user.id, role_id=admin_role.id).first():
                user_role = UserRole(user_id=admin_user.id, role_id=admin_role.id)
                db.session.add(user_role)
                db.session.commit()
        
        # Create default cash register if it doesn't exist
        default_register = POSCashRegister.query.filter_by(name='Main Register').first()
        if not default_register:
            print("Creating default cash register...")
            default_register = POSCashRegister(
                name='Main Register',
                balance=0.0
            )
            db.session.add(default_register)
            db.session.commit()
            print(f"Default cash register created: {default_register.name}")
        
        # Create required stock locations if they don't exist
        # Check for SHOP location (used in POS transactions)
        shop_location = StockLocation.query.filter_by(code='SHOP').first()
        if not shop_location:
            print("Creating SHOP stock location...")
            shop_location = StockLocation(
                name='Shop Floor',
                code='SHOP',
                location_type='internal'
            )
            db.session.add(shop_location)
            db.session.commit()
            print(f"SHOP stock location created: {shop_location.name}")
        
        # Check for Customer location
        customer_location = StockLocation.query.filter_by(location_type='customer').first()
        if not customer_location:
            print("Creating Customer stock location...")
            customer_location = StockLocation(
                name='Customer',
                code='CUST',
                location_type='customer'
            )
            db.session.add(customer_location)
            db.session.commit()
            print(f"Customer stock location created: {customer_location.name}")
        
        print("Database setup completed successfully!")
        print("Admin user created with username: 'admin' and password: 'admin123'")

if __name__ == '__main__':
    setup_database()
