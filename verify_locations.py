import sqlite3
import os

# Path to the database file
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'odoo_clone.db')

# Connect to the database
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check branches
print("\n=== BRANCHES ===")
cursor.execute("SELECT * FROM branches")
branches = cursor.fetchall()
if branches:
    for branch in branches:
        print(f"ID: {branch['id']}, Name: {branch['name']}, Active: {branch['is_active']}")
else:
    print("No branches found in the database.")

# Check stock locations
print("\n=== STOCK LOCATIONS ===")
cursor.execute("SELECT * FROM stock_locations")
locations = cursor.fetchall()
if locations:
    for loc in locations:
        branch_name = "No Branch"
        if loc['branch_id']:
            cursor.execute("SELECT name FROM branches WHERE id = ?", (loc['branch_id'],))
            branch = cursor.fetchone()
            if branch:
                branch_name = branch['name']
        
        print(f"ID: {loc['id']}, Name: {loc['name']}, Type: {loc['location_type']}, Branch ID: {loc['branch_id']}, Branch: {branch_name}")
else:
    print("No stock locations found in the database.")

# Close the connection
conn.close()
