import sqlite3
import os
from datetime import datetime

# Path to the database file
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'odoo_clone.db')

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if branches table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='branches'")
if not cursor.fetchone():
    print("Creating branches table...")
    cursor.execute('''
    CREATE TABLE branches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        location TEXT,
        address TEXT,
        phone TEXT,
        email TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Insert default branches
    branches = [
        ('Main Branch', 'Headquarters', '123 Main St', '555-1234', 'main@example.com', 1),
        ('Branch1', 'Downtown', '456 First Ave', '555-5678', 'branch1@example.com', 1),
        ('Branch2', 'Uptown', '789 Second St', '555-9012', 'branch2@example.com', 1)
    ]
    
    cursor.executemany('''
    INSERT INTO branches (name, location, address, phone, email, is_active)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', branches)
    
    print("Branches created successfully!")
else:
    print("Branches table already exists.")
    # Check if there are any branches
    cursor.execute("SELECT COUNT(*) FROM branches")
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Insert default branches if none exist
        branches = [
            ('Main Branch', 'Headquarters', '123 Main St', '555-1234', 'main@example.com', 1),
            ('Branch1', 'Downtown', '456 First Ave', '555-5678', 'branch1@example.com', 1),
            ('Branch2', 'Uptown', '789 Second St', '555-9012', 'branch2@example.com', 1)
        ]
        
        cursor.executemany('''
        INSERT INTO branches (name, location, address, phone, email, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', branches)
        
        print("Default branches added!")
    else:
        print(f"Found {count} existing branches.")
        cursor.execute("SELECT id, name FROM branches")
        branches = cursor.fetchall()
        for branch in branches:
            print(f"ID: {branch[0]}, Name: {branch[1]}")

# Now check if stock_locations table has branch_id column
cursor.execute("PRAGMA table_info(stock_locations)")
columns = cursor.fetchall()
has_branch_id = any(column[1] == 'branch_id' for column in columns)

if not has_branch_id:
    print("\nAdding branch_id column to stock_locations table...")
    cursor.execute("ALTER TABLE stock_locations ADD COLUMN branch_id INTEGER REFERENCES branches(id)")
    print("Column added successfully!")
else:
    print("\nbranch_id column already exists in stock_locations table.")

# Assign branches to locations if not already assigned
print("\nAssigning branches to locations...")
cursor.execute("SELECT id, name FROM stock_locations WHERE branch_id IS NULL")
locations = cursor.fetchall()

if locations:
    # Get the Main Branch ID
    cursor.execute("SELECT id FROM branches WHERE name = 'Main Branch'")
    main_branch = cursor.fetchone()
    main_branch_id = main_branch[0] if main_branch else 1
    
    # Get Branch1 ID
    cursor.execute("SELECT id FROM branches WHERE name = 'Branch1'")
    branch1 = cursor.fetchone()
    branch1_id = branch1[0] if branch1 else 2
    
    # Assign Main Branch to internal locations and Branch1 to some others
    for loc_id, loc_name in locations:
        if 'Main' in loc_name:
            branch_id = main_branch_id
        elif 'Stock' in loc_name:
            branch_id = main_branch_id
        else:
            branch_id = branch1_id
        
        cursor.execute("UPDATE stock_locations SET branch_id = ? WHERE id = ?", (branch_id, loc_id))
        print(f"Assigned location '{loc_name}' to branch ID {branch_id}")
    
    print("Locations updated with branch assignments!")
else:
    print("All locations already have branch assignments.")

# Commit changes and close connection
conn.commit()
conn.close()

print("\nDone! Branches and location assignments have been set up.")
