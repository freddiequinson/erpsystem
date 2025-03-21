import sqlite3
import os

# Path to the database file
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'odoo_clone.db')

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("\n=== DATABASE TABLES ===")
if tables:
    for table in tables:
        print(f"Table: {table[0]}")
        
        # Get column info for each table
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        print("Columns:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        print()
else:
    print("No tables found in the database.")

# Close the connection
conn.close()
