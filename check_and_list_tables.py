"""
Check and list all tables in the database
"""
import sqlite3
from config import Config

def check_tables():
    # Get the database file path from config
    db_uri = Config.SQLALCHEMY_DATABASE_URI
    
    # Extract the database filename from the URI
    if db_uri.startswith('sqlite:///'):
        db_filename = db_uri.replace('sqlite:///', '')
        print(f"Using database file: {db_filename}")
        
        # Connect to the database
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()
        
        # List all tables in the database
        print("\nTables in the database:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = cursor.fetchall()
        
        if tables:
            for table in tables:
                # Get row count for each table
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                row_count = cursor.fetchone()[0]
                print(f"- {table[0]} ({row_count} rows)")
        else:
            print("No tables found in the database.")
        
        # Close the connection
        conn.close()
    else:
        print("Non-SQLite database detected. This script only works with SQLite.")

if __name__ == "__main__":
    check_tables()
