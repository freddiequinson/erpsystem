"""
Initialize Fresh Database
This script ensures a completely fresh database is created with all necessary tables and minimal data
"""
import os
import sys
import sqlite3
import subprocess
from pathlib import Path
from config import Config

def initialize_fresh_db():
    print("INITIALIZING FRESH DATABASE")
    print("==========================")
    
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
        
        # Run app.py to create the database with all tables
        print("\nRunning app.py to create database tables...")
        try:
            # Import the create_app function and create the database
            from app import create_app, db
            app = create_app('development')
            with app.app_context():
                db.create_all()
                print("All database tables created successfully!")
        except Exception as e:
            print(f"Error creating database tables: {e}")
            return False
        
        # Run init_db.py to initialize with minimal data
        print("\nRunning init_db.py to initialize with minimal data...")
        try:
            # Run init_db.py as a separate process
            result = subprocess.run([sys.executable, "init_db.py"], capture_output=True, text=True)
            print(result.stdout)
            if result.returncode != 0:
                print(f"Error running init_db.py: {result.stderr}")
                return False
        except Exception as e:
            print(f"Error running init_db.py: {e}")
            return False
        
        # Run fix_cash_register.py to set up cash registers
        print("\nSetting up cash registers...")
        try:
            result = subprocess.run([sys.executable, "fix_cash_register.py"], capture_output=True, text=True)
            print(result.stdout)
            if result.returncode != 0:
                print(f"Error running fix_cash_register.py: {result.stderr}")
                return False
        except Exception as e:
            print(f"Error running fix_cash_register.py: {e}")
            return False
        
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
    success = initialize_fresh_db()
    if success:
        print("\n✅ FRESH DATABASE INITIALIZED SUCCESSFULLY")
        print("The system is now ready for new use with minimal data.")
    else:
        print("\n❌ Database initialization failed. Please check the errors above.")
