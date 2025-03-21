"""
Complete database reset script
This script will completely remove the existing database and initialize a fresh one
"""
import os
import sys
import shutil
from pathlib import Path

def complete_reset():
    print("Starting complete database reset...")
    
    # Get the database file path from config
    from config import Config
    db_uri = Config.SQLALCHEMY_DATABASE_URI
    
    # Extract the database filename from the URI
    # Assuming SQLite URI format: sqlite:///filename.db
    if db_uri.startswith('sqlite:///'):
        db_filename = db_uri.replace('sqlite:///','')
        db_path = Path(db_filename)
        
        # Check if the file exists
        if db_path.exists():
            print(f"Removing existing database file: {db_path}")
            try:
                os.remove(db_path)
                print("Database file removed successfully.")
            except Exception as e:
                print(f"Error removing database file: {e}")
                return False
        else:
            print("Database file does not exist. Will create a new one.")
    else:
        print("Non-SQLite database detected. Please manually reset your database.")
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
    
    # Run the initialization script
    print("\nInitializing new database...")
    try:
        # Import and run init_db
        from init_db import init_db
        init_db()
        print("Database initialized successfully!")
        
        # Run the fix_cash_register script to set up cash registers
        print("\nSetting up cash registers...")
        import subprocess
        subprocess.run([sys.executable, "fix_cash_register.py"], check=True)
        print("Cash registers set up successfully!")
        
        return True
    except Exception as e:
        print(f"Error during initialization: {e}")
        return False

if __name__ == "__main__":
    success = complete_reset()
    if success:
        print("\n✅ Complete database reset successful! The system is now fresh for new use.")
    else:
        print("\n❌ Database reset failed. Please check the errors above.")
