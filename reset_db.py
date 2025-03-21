"""
Script to reset the database for a fresh start
This will delete the current database and run the initialization script
"""
import os
import sys
from pathlib import Path

def reset_database():
    print("Resetting database for a fresh start...")
    
    # Get the database file path from config
    from config import Config
    db_uri = Config.SQLALCHEMY_DATABASE_URI
    
    # Extract the database filename from the URI
    # Assuming SQLite URI format: sqlite:///filename.db
    if db_uri.startswith('sqlite:///'):
        db_filename = db_uri.replace('sqlite:///', '')
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
            print("Database file does not exist. Creating a new one.")
    else:
        print("Non-SQLite database detected. Please manually reset your database.")
        return False
    
    # Run the initialization script
    print("Initializing new database...")
    try:
        from init_db import init_db
        init_db()
        print("Database initialized successfully!")
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

if __name__ == "__main__":
    success = reset_database()
    if success:
        print("Database reset complete. You can now deploy the application with a fresh database.")
    else:
        print("Database reset failed. Please check the errors above.")
