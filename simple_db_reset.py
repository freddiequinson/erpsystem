"""
Simple Database Reset
This script completely resets the database by:
1. Deleting the database file
2. Running the app once to create the database structure
3. Adding minimal data directly using SQLite
"""
import os
import sys
import sqlite3
import subprocess
from pathlib import Path
from config import Config

def simple_db_reset():
    print("SIMPLE DATABASE RESET")
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
        
        # Run create_db_tables.py to create the database structure
        print("\nCreating database tables...")
        try:
            # Create a simple script to create tables
            with open("create_tables_only.py", "w") as f:
                f.write("""
from app import create_app, db

def create_tables():
    app = create_app('development')
    with app.app_context():
        db.create_all()
        print("All database tables created successfully!")

if __name__ == '__main__':
    create_tables()
""")
            
            # Run the script
            result = subprocess.run([sys.executable, "create_tables_only.py"], capture_output=True, text=True)
            print(result.stdout)
            if result.returncode != 0:
                print(f"Error creating tables: {result.stderr}")
                return False
        except Exception as e:
            print(f"Error creating database tables: {e}")
            return False
        
        # Create cash registers table and add minimal data
        print("\nSetting up cash registers...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create pos_cash_registers table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pos_cash_registers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(64) NOT NULL,
            balance FLOAT DEFAULT 0.0,
            branch_id INTEGER
        )
        """)
        
        # Add cash registers
        cursor.execute("DELETE FROM pos_cash_registers")  # Clear any existing data
        cursor.execute("INSERT INTO pos_cash_registers (name, balance, branch_id) VALUES (?, ?, ?)", 
                      ("Main Register", 0.0, 1))
        cursor.execute("INSERT INTO pos_cash_registers (name, balance, branch_id) VALUES (?, ?, ?)", 
                      ("Secondary Register", 0.0, 1))
        
        # Commit changes
        conn.commit()
        print("Cash registers set up successfully!")
        
        # Verify the database
        print("\nVerifying database contents...")
        
        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        print(f"Database contains {len(tables)} tables:")
        for table_name in table_names:
            print(f"- {table_name}")
        
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
    success = simple_db_reset()
    if success:
        print("\n✅ DATABASE COMPLETELY RESET WITH MINIMAL DATA")
        print("The system is now ready for new use with minimal initial data.")
    else:
        print("\n❌ Database reset failed. Please check the errors above.")
