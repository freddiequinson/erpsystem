import sqlite3
import os
from datetime import datetime

# Path to the database file
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'odoo_clone.db')

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if warehouses table exists, create if not
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='warehouses'")
if not cursor.fetchone():
    print("Creating warehouses table...")
    cursor.execute('''
    CREATE TABLE warehouses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT NOT NULL UNIQUE,
        address TEXT
    )
    ''')
    
    # Insert default warehouse
    cursor.execute('''
    INSERT INTO warehouses (name, code, address)
    VALUES (?, ?, ?)
    ''', ('Main Warehouse', 'WH01', '123 Main St'))
    
    print("Warehouses table created successfully!")
else:
    print("Warehouses table already exists.")

# Check if stock_locations table exists, create if not
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stock_locations'")
if not cursor.fetchone():
    print("Creating stock_locations table...")
    cursor.execute('''
    CREATE TABLE stock_locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        location_type TEXT DEFAULT 'internal',
        parent_id INTEGER,
        warehouse_id INTEGER,
        is_active INTEGER DEFAULT 1,
        branch_id INTEGER,
        FOREIGN KEY (parent_id) REFERENCES stock_locations(id),
        FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
        FOREIGN KEY (branch_id) REFERENCES branches(id)
    )
    ''')
    
    # Get warehouse ID
    cursor.execute("SELECT id FROM warehouses WHERE code = 'WH01'")
    result = cursor.fetchone()
    if result:
        warehouse_id = result[0]
    else:
        # Insert default warehouse if it doesn't exist
        cursor.execute('''
        INSERT INTO warehouses (name, code, address)
        VALUES (?, ?, ?)
        ''', ('Main Warehouse', 'WH01', '123 Main St'))
        warehouse_id = cursor.lastrowid
        print("Created Main Warehouse with ID:", warehouse_id)
    
    # Get branch IDs
    cursor.execute("SELECT id FROM branches WHERE name = 'Main Branch'")
    result = cursor.fetchone()
    if result:
        main_branch_id = result[0]
    else:
        # Insert Main Branch if it doesn't exist
        cursor.execute('''
        INSERT INTO branches (name, location, address, is_active)
        VALUES (?, ?, ?, ?)
        ''', ('Main Branch', 'Headquarters', '123 Main St', 1))
        main_branch_id = cursor.lastrowid
        print("Created Main Branch with ID:", main_branch_id)
    
    cursor.execute("SELECT id FROM branches WHERE name = 'Branch1'")
    result = cursor.fetchone()
    if result:
        branch1_id = result[0]
    else:
        # Insert Branch1 if it doesn't exist
        cursor.execute('''
        INSERT INTO branches (name, location, address, is_active)
        VALUES (?, ?, ?, ?)
        ''', ('Branch1', 'Downtown', '456 First Ave', 1))
        branch1_id = cursor.lastrowid
        print("Created Branch1 with ID:", branch1_id)
    
    # Insert default stock locations
    locations = [
        # Main Branch locations
        ('Stock', 'internal', None, warehouse_id, 1, main_branch_id),
        ('Suppliers', 'supplier', None, warehouse_id, 1, main_branch_id),
        ('Customers', 'customer', None, warehouse_id, 1, main_branch_id),
        ('Inventory Loss', 'inventory_loss', None, warehouse_id, 1, main_branch_id),
        ('Production', 'production', None, warehouse_id, 1, main_branch_id),
        
        # Branch1 locations
        ('Branch1 Stock', 'internal', None, warehouse_id, 1, branch1_id),
        ('Branch1 Suppliers', 'supplier', None, warehouse_id, 1, branch1_id),
        ('Branch1 Customers', 'customer', None, warehouse_id, 1, branch1_id)
    ]
    
    cursor.executemany('''
    INSERT INTO stock_locations (name, location_type, parent_id, warehouse_id, is_active, branch_id)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', locations)
    
    print("Stock locations created successfully!")
else:
    print("Stock_locations table already exists.")
    # Check if there are any locations
    cursor.execute("SELECT COUNT(*) FROM stock_locations")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("No stock locations found, creating default locations...")
        
        # Get warehouse ID
        cursor.execute("SELECT id FROM warehouses WHERE code = 'WH01'")
        result = cursor.fetchone()
        if result:
            warehouse_id = result[0]
        else:
            # Insert default warehouse if it doesn't exist
            cursor.execute('''
            INSERT INTO warehouses (name, code, address)
            VALUES (?, ?, ?)
            ''', ('Main Warehouse', 'WH01', '123 Main St'))
            warehouse_id = cursor.lastrowid
            print("Created Main Warehouse with ID:", warehouse_id)
        
        # Get branch IDs
        cursor.execute("SELECT id FROM branches WHERE name = 'Main Branch'")
        result = cursor.fetchone()
        if result:
            main_branch_id = result[0]
        else:
            # Insert Main Branch if it doesn't exist
            cursor.execute('''
            INSERT INTO branches (name, location, address, is_active)
            VALUES (?, ?, ?, ?)
            ''', ('Main Branch', 'Headquarters', '123 Main St', 1))
            main_branch_id = cursor.lastrowid
            print("Created Main Branch with ID:", main_branch_id)
        
        cursor.execute("SELECT id FROM branches WHERE name = 'Branch1'")
        result = cursor.fetchone()
        if result:
            branch1_id = result[0]
        else:
            # Insert Branch1 if it doesn't exist
            cursor.execute('''
            INSERT INTO branches (name, location, address, is_active)
            VALUES (?, ?, ?, ?)
            ''', ('Branch1', 'Downtown', '456 First Ave', 1))
            branch1_id = cursor.lastrowid
            print("Created Branch1 with ID:", branch1_id)
        
        # Insert default stock locations
        locations = [
            # Main Branch locations
            ('Stock', 'internal', None, warehouse_id, 1, main_branch_id),
            ('Suppliers', 'supplier', None, warehouse_id, 1, main_branch_id),
            ('Customers', 'customer', None, warehouse_id, 1, main_branch_id),
            ('Inventory Loss', 'inventory_loss', None, warehouse_id, 1, main_branch_id),
            ('Production', 'production', None, warehouse_id, 1, main_branch_id),
            
            # Branch1 locations
            ('Branch1 Stock', 'internal', None, warehouse_id, 1, branch1_id),
            ('Branch1 Suppliers', 'supplier', None, warehouse_id, 1, branch1_id),
            ('Branch1 Customers', 'customer', None, warehouse_id, 1, branch1_id)
        ]
        
        cursor.executemany('''
        INSERT INTO stock_locations (name, location_type, parent_id, warehouse_id, is_active, branch_id)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', locations)
        
        print("Default stock locations created!")
    else:
        print(f"Found {count} existing stock locations.")
        cursor.execute("SELECT id, name, branch_id FROM stock_locations")
        locations = cursor.fetchall()
        for loc in locations:
            branch_name = "No Branch"
            if loc[2]:
                cursor.execute("SELECT name FROM branches WHERE id = ?", (loc[2],))
                branch = cursor.fetchone()
                if branch:
                    branch_name = branch[0]
            print(f"ID: {loc[0]}, Name: {loc[1]}, Branch: {branch_name}")

# Check if products table exists, create if not
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
if not cursor.fetchone():
    print("\nCreating products table...")
    cursor.execute('''
    CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        sku TEXT UNIQUE,
        barcode TEXT,
        category_id INTEGER,
        cost_price REAL,
        sale_price REAL,
        is_active INTEGER DEFAULT 1,
        branch_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        image_path TEXT,
        FOREIGN KEY (branch_id) REFERENCES branches(id)
    )
    ''')
    
    # Insert sample products
    products = [
        ('Product 1', 'Description for Product 1', 'SKU001', 'BARCODE001', None, 10.0, 15.0, 1, main_branch_id),
        ('Product 2', 'Description for Product 2', 'SKU002', 'BARCODE002', None, 20.0, 30.0, 1, main_branch_id),
        ('Product 3', 'Description for Product 3', 'SKU003', 'BARCODE003', None, 5.0, 8.0, 1, branch1_id)
    ]
    
    cursor.executemany('''
    INSERT INTO products (name, description, sku, barcode, category_id, cost_price, sale_price, is_active, branch_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', products)
    
    print("Products table created successfully!")
else:
    print("\nProducts table already exists.")

# Check if stock_moves table exists, create if not
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stock_moves'")
if not cursor.fetchone():
    print("\nCreating stock_moves table...")
    cursor.execute('''
    CREATE TABLE stock_moves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        source_location_id INTEGER NOT NULL,
        destination_location_id INTEGER NOT NULL,
        quantity REAL NOT NULL,
        state TEXT DEFAULT 'draft',
        reference TEXT,
        reference_type TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        scheduled_date TIMESTAMP,
        effective_date TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products(id),
        FOREIGN KEY (source_location_id) REFERENCES stock_locations(id),
        FOREIGN KEY (destination_location_id) REFERENCES stock_locations(id)
    )
    ''')
    
    print("Stock_moves table created successfully!")
else:
    print("\nStock_moves table already exists.")

# Commit changes and close connection
conn.commit()
conn.close()

print("\nDone! Database tables have been set up.")
