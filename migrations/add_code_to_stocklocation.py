import sqlite3
import os

# Get the database path
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance', 'odoo.db')

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if the code column already exists
cursor.execute("PRAGMA table_info(stock_locations)")
columns = cursor.fetchall()
column_names = [column[1] for column in columns]

if 'code' not in column_names:
    # Add the code column to the stock_locations table
    cursor.execute("ALTER TABLE stock_locations ADD COLUMN code TEXT")
    print("Added 'code' column to stock_locations table")
else:
    print("'code' column already exists in stock_locations table")

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Migration completed successfully")
