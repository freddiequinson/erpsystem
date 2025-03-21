"""
Force clear all data from the database
This script will delete all data from all tables while preserving the schema
"""
import os
import sys
import sqlite3
from pathlib import Path
from config import Config

def force_clear_all_data():
    print("FORCE CLEARING ALL DATA FROM DATABASE")
    print("====================================")
    
    # Get the database file path from config
    db_uri = Config.SQLALCHEMY_DATABASE_URI
    
    # Extract the database filename from the URI
    if db_uri.startswith('sqlite:///'):
        db_filename = db_uri.replace('sqlite:///', '')
        db_path = Path(db_filename)
        
        if not db_path.exists():
            print(f"Database file {db_path} does not exist. Nothing to clear.")
            return False
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = cursor.fetchall()
        
        # Disable foreign key constraints temporarily
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # Begin transaction
        cursor.execute("BEGIN TRANSACTION")
        
        try:
            # Delete all data from each table
            for table in tables:
                table_name = table[0]
                print(f"Clearing all data from table: {table_name}")
                cursor.execute(f"DELETE FROM {table_name}")
            
            # Commit the transaction
            conn.commit()
            print("\nAll data has been cleared from all tables.")
            
            # Re-enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Run the initialization script to add back essential data
            print("\nRe-initializing database with fresh data...")
            from init_db import init_db
            init_db()
            
            # Set up cash registers
            print("\nSetting up cash registers...")
            import subprocess
            subprocess.run([sys.executable, "fix_cash_register.py"], check=True)
            
            return True
            
        except Exception as e:
            # Rollback in case of error
            conn.rollback()
            print(f"Error clearing data: {e}")
            return False
        finally:
            # Close the connection
            conn.close()
    else:
        print("Non-SQLite database detected. This script only works with SQLite.")
        return False

if __name__ == "__main__":
    success = force_clear_all_data()
    if success:
        print("\n✅ DATABASE COMPLETELY CLEARED AND RESET WITH FRESH DATA")
        print("The system is now ready for new use with no previous data.")
    else:
        print("\n❌ Database reset failed. Please check the errors above.")
