"""
Complete database rebuild script
This script will delete the database file and create a new one from scratch
"""
import os
import sys
import sqlite3
import shutil
from pathlib import Path
from config import Config

def complete_rebuild():
    print("COMPLETE DATABASE REBUILD")
    print("========================")
    
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
        print("\nInitializing database with fresh data...")
        try:
            # Import and run init_db
            from init_db import init_db
            init_db()
            print("Database initialized successfully!")
            
            # Verify the database was initialized correctly
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check for products table and count
            cursor.execute("SELECT COUNT(*) FROM products")
            product_count = cursor.fetchone()[0]
            print(f"\nVerification: Database has {product_count} products")
            
            # Check for users
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            print(f"Verification: Database has {user_count} users")
            
            conn.close()
            
            return True
        except Exception as e:
            print(f"Error during initialization: {e}")
            return False
    else:
        print("Non-SQLite database detected. This script only works with SQLite.")
        return False

if __name__ == "__main__":
    success = complete_rebuild()
    if success:
        print("\n✅ DATABASE COMPLETELY REBUILT WITH FRESH DATA")
        print("The system is now ready for new use with minimal default data.")
    else:
        print("\n❌ Database rebuild failed. Please check the errors above.")
