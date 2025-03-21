"""
Reset All Data Script
This script completely resets the database by:
1. Deleting the database file
2. Creating a new empty database
3. Running the initialization script with minimal data
"""
import os
import sys
import sqlite3
import shutil
from pathlib import Path
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

def reset_all_data():
    print("COMPLETE DATABASE RESET")
    print("======================")
    
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
        
        # Create a new empty database
        print("\nCreating new empty database...")
        conn = sqlite3.connect(db_path)
        conn.close()
        print(f"Created new empty database file: {db_path}")
        
        # Run the initialization script
        print("\nInitializing database with minimal data...")
        try:
            # Import and run init_db
            from init_db import init_db
            init_db()
            print("Database initialized successfully!")
            
            # Set up cash registers
            print("\nSetting up cash registers...")
            import subprocess
            subprocess.run([sys.executable, "fix_cash_register.py"], check=True)
            
            # Verify the database
            print("\nVerifying database contents...")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # List all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = cursor.fetchall()
            print(f"Database contains {len(tables)} tables")
            
            # Check for products
            try:
                cursor.execute("SELECT COUNT(*) FROM products")
                product_count = cursor.fetchone()[0]
                print(f"Products: {product_count}")
            except sqlite3.OperationalError:
                print("Products table not found")
            
            # Check for users
            try:
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]
                print(f"Users: {user_count}")
            except sqlite3.OperationalError:
                print("Users table not found")
            
            # Check for cash registers
            try:
                cursor.execute("SELECT COUNT(*) FROM pos_cash_registers")
                register_count = cursor.fetchone()[0]
                print(f"Cash Registers: {register_count}")
            except sqlite3.OperationalError:
                print("Cash Registers table not found")
            
            conn.close()
            
            return True
        except Exception as e:
            print(f"Error during initialization: {e}")
            return False
    else:
        print("Non-SQLite database detected. This script only works with SQLite.")
        return False

if __name__ == "__main__":
    success = reset_all_data()
    if success:
        print("\n✅ DATABASE COMPLETELY RESET WITH MINIMAL DATA")
        print("The system is now ready for new use.")
    else:
        print("\n❌ Database reset failed. Please check the errors above.")
