"""
Direct Database Reset
This script directly resets the database by:
1. Deleting the database file
2. Creating a new database with all tables
3. Adding minimal initial data
"""
import os
import sys
import sqlite3
from pathlib import Path
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

def direct_db_reset():
    print("DIRECT DATABASE RESET")
    print("====================")
    
    # Get the database file path from config
    db_uri = Config.SQLALCHEMY_DATABASE_URI
    
    # Extract the database filename from the URI
    if db_uri.startswith('sqlite:///'):
        db_filename = db_uri.replace('sqlite:///', '')
        db_path = Path(db_filename)
        
        # Delete the database file if it exists
        if db_path.exists():
            print(f"Deleting existing database file: {db_path}")
            try:
                os.remove(db_path)
                print("Database file deleted successfully.")
            except Exception as e:
                print(f"Error deleting database file: {e}")
                return False
        
        # Also remove any SQLite journal or WAL files
        for ext in ['-journal', '-wal', '-shm']:
            journal_path = str(db_path) + ext
            if os.path.exists(journal_path):
                try:
                    os.remove(journal_path)
                    print(f"Removed {journal_path}")
                except Exception as e:
                    print(f"Error removing {journal_path}: {e}")
        
        # Create a new Flask app with the database configuration
        print("\nCreating new Flask app and database...")
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db = SQLAlchemy(app)
        
        # Define minimal models for essential tables
        class User(db.Model):
            __tablename__ = 'users'
            id = db.Column(db.Integer, primary_key=True)
            username = db.Column(db.String(64), unique=True, nullable=False)
            email = db.Column(db.String(120), unique=True, nullable=False)
            password_hash = db.Column(db.String(128), nullable=False)
            is_active = db.Column(db.Boolean, default=True)
            created_at = db.Column(db.DateTime)
        
        class Role(db.Model):
            __tablename__ = 'roles'
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(64), unique=True, nullable=False)
            description = db.Column(db.String(255))
        
        class UserRole(db.Model):
            __tablename__ = 'user_roles'
            id = db.Column(db.Integer, primary_key=True)
            user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
            role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
        
        class Product(db.Model):
            __tablename__ = 'products'
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(128), nullable=False)
            description = db.Column(db.Text)
            barcode = db.Column(db.String(64))
            cost_price = db.Column(db.Float, default=0.0)
            sale_price = db.Column(db.Float, default=0.0)
            is_active = db.Column(db.Boolean, default=True)
        
        class POSCashRegister(db.Model):
            __tablename__ = 'pos_cash_registers'
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String(64), nullable=False)
            balance = db.Column(db.Float, default=0.0)
            branch_id = db.Column(db.Integer)
        
        # Create all tables
        with app.app_context():
            db.create_all()
            print("All tables created successfully!")
            
            # Add minimal data
            print("\nAdding minimal data...")
            
            # Add admin user
            admin_user = User(
                username='admin',
                email='admin@example.com',
                password_hash='$2b$12$1xxxxxxxxxxxxxxxxxxxxuZLbwxnpY0o58unSvIPxddLxGystU.O',  # admin123
                is_active=True,
                created_at=db.func.now()
            )
            db.session.add(admin_user)
            
            # Add roles
            admin_role = Role(name='Admin', description='Administrator with full access')
            db.session.add(admin_role)
            
            # Add user role
            db.session.flush()  # Flush to get IDs
            user_role = UserRole(user_id=admin_user.id, role_id=admin_role.id)
            db.session.add(user_role)
            
            # Add sample product
            sample_product = Product(
                name='Sample Product',
                description='A sample product for testing',
                barcode='123456789',
                cost_price=10.0,
                sale_price=20.0,
                is_active=True
            )
            db.session.add(sample_product)
            
            # Add cash registers
            main_register = POSCashRegister(name='Main Register', balance=0.0, branch_id=1)
            secondary_register = POSCashRegister(name='Secondary Register', balance=0.0, branch_id=1)
            db.session.add_all([main_register, secondary_register])
            
            # Commit changes
            db.session.commit()
            print("Minimal data added successfully!")
        
        # Verify the database
        print("\nVerifying database contents...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        print(f"Database contains {len(tables)} tables:")
        for table_name in table_names:
            print(f"- {table_name}")
        
        # Check for products
        if 'products' in table_names:
            cursor.execute("SELECT COUNT(*) FROM products")
            product_count = cursor.fetchone()[0]
            print(f"Products: {product_count}")
        else:
            print("Products table not found")
        
        # Check for users
        if 'users' in table_names:
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            print(f"Users: {user_count}")
        else:
            print("Users table not found")
        
        # Check for cash registers
        if 'pos_cash_registers' in table_names:
            cursor.execute("SELECT COUNT(*) FROM pos_cash_registers")
            register_count = cursor.fetchone()[0]
            print(f"Cash Registers: {register_count}")
        else:
            print("Cash Registers table not found")
        
        conn.close()
        
        return True
    else:
        print("Non-SQLite database detected. This script only works with SQLite.")
        return False

if __name__ == "__main__":
    success = direct_db_reset()
    if success:
        print("\n✅ DATABASE COMPLETELY RESET WITH MINIMAL DATA")
        print("The system is now ready for new use with minimal initial data.")
    else:
        print("\n❌ Database reset failed. Please check the errors above.")
