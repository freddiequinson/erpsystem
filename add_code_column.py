import sqlite3
import os

# Get the database path
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'odoo.db')
print(f"Database path: {db_path}")

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if the stock_locations table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stock_locations'")
if cursor.fetchone():
    # Check if the code column already exists
    cursor.execute("PRAGMA table_info(stock_locations)")
    columns = cursor.fetchall()
    column_names = [column[1] for column in columns]
    
    print(f"Columns in stock_locations table: {column_names}")
    
    if 'code' not in column_names:
        # Add the code column to the stock_locations table
        print("Adding 'code' column to stock_locations table...")
        cursor.execute("ALTER TABLE stock_locations ADD COLUMN code TEXT")
        conn.commit()
        print("Added 'code' column to stock_locations table")
    else:
        print("'code' column already exists in stock_locations table")
else:
    print("stock_locations table does not exist")

# Commit the changes and close the connection
conn.close()

print("Script completed")
