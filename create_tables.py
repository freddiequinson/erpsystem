from app import create_app
from extensions import db
from modules.inventory.models import Category, UnitOfMeasure, Product, Warehouse, StockLocation, StockMove, Inventory, InventoryLine
import sqlite3
import os

def create_tables():
    # Get the database path
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'odoo.db')
    print(f"Database path: {db_path}")
    
    # Connect to the database directly using sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create stock_locations table
        print("Creating stock_locations table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(64) NOT NULL,
            code VARCHAR(20),
            warehouse_id INTEGER,
            parent_id INTEGER,
            location_type VARCHAR(20) NOT NULL,
            FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
            FOREIGN KEY (parent_id) REFERENCES stock_locations(id)
        )
        ''')
        
        # Create warehouses table if it doesn't exist
        print("Creating warehouses table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS warehouses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(64) NOT NULL,
            code VARCHAR(10) NOT NULL UNIQUE,
            address VARCHAR(255)
        )
        ''')
        
        # Create stock_moves table if it doesn't exist
        print("Creating stock_moves table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_moves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            source_location_id INTEGER NOT NULL,
            destination_location_id INTEGER NOT NULL,
            quantity FLOAT NOT NULL,
            state VARCHAR(20) DEFAULT 'draft',
            reference VARCHAR(64),
            reference_type VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            scheduled_date TIMESTAMP,
            effective_date TIMESTAMP,
            date TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (source_location_id) REFERENCES stock_locations(id),
            FOREIGN KEY (destination_location_id) REFERENCES stock_locations(id)
        )
        ''')
        
        # Create default locations if they don't exist
        print("Creating default locations...")
        
        # Check if supplier location exists
        cursor.execute("SELECT id FROM stock_locations WHERE location_type='supplier' LIMIT 1")
        supplier_location = cursor.fetchone()
        if not supplier_location:
            cursor.execute("INSERT INTO stock_locations (name, location_type, code) VALUES ('Supplier', 'supplier', 'SUP')")
            print("Created supplier location")
        
        # Check if inventory loss location exists
        cursor.execute("SELECT id FROM stock_locations WHERE location_type='inventory_loss' LIMIT 1")
        inventory_loss_location = cursor.fetchone()
        if not inventory_loss_location:
            cursor.execute("INSERT INTO stock_locations (name, location_type, code) VALUES ('Inventory Loss', 'inventory_loss', 'INV-LOSS')")
            print("Created inventory loss location")
        
        # Check if warehouse exists
        cursor.execute("SELECT id FROM warehouses LIMIT 1")
        warehouse = cursor.fetchone()
        if not warehouse:
            cursor.execute("INSERT INTO warehouses (name, code, address) VALUES ('Main Warehouse', 'MAIN', 'Default Address')")
            cursor.execute("SELECT id FROM warehouses LIMIT 1")
            warehouse_id = cursor.fetchone()[0]
            print(f"Created main warehouse with ID {warehouse_id}")
            
            # Create internal location for the warehouse
            cursor.execute(f"INSERT INTO stock_locations (name, warehouse_id, location_type, code) VALUES ('Main Stock', {warehouse_id}, 'internal', 'STOCK')")
            print("Created internal location for main warehouse")
        else:
            warehouse_id = warehouse[0]
            # Check if internal location exists for this warehouse
            cursor.execute(f"SELECT id FROM stock_locations WHERE warehouse_id={warehouse_id} AND location_type='internal' LIMIT 1")
            internal_location = cursor.fetchone()
            if not internal_location:
                cursor.execute(f"INSERT INTO stock_locations (name, warehouse_id, location_type, code) VALUES ('Main Stock', {warehouse_id}, 'internal', 'STOCK')")
                print("Created internal location for existing warehouse")
        
        # Commit the changes
        conn.commit()
        print("Tables created successfully")
        
    except Exception as e:
        print(f"Error creating tables: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    create_tables()
