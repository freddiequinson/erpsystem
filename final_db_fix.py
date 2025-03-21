import sqlite3
import os
import shutil
import time

def final_database_fix():
    """Final approach to fix database structure issues"""
    db_path = 'erp_system.db'
    backup_path = f'erp_system_backup_{int(time.time())}.db'
    
    # Create a backup
    if os.path.exists(db_path):
        print(f"Creating backup of existing database to {backup_path}")
        shutil.copy2(db_path, backup_path)
        print("Backup created successfully")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get a list of all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Found {len(tables)} tables in the database")
    
    # Make a completely fresh database for returns
    print("Completely recreating returns-related tables...")
    cursor.execute("DROP TABLE IF EXISTS quality_checks")
    cursor.execute("DROP TABLE IF EXISTS pos_return_lines")
    cursor.execute("DROP TABLE IF EXISTS pos_returns")
    conn.commit()
    
    # Create the returns tables
    print("Creating pos_returns table...")
    cursor.execute('''
    CREATE TABLE pos_returns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(64),
        original_order_id INTEGER,
        customer_name VARCHAR(128),
        customer_phone VARCHAR(64),
        return_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total_amount FLOAT DEFAULT 0.0,
        refund_amount FLOAT DEFAULT 0.0,
        return_type VARCHAR(20),
        refund_method VARCHAR(20),
        notes TEXT,
        created_by INTEGER,
        state VARCHAR(20) DEFAULT 'draft',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    print("Creating pos_return_lines table WITH ALL NEEDED COLUMNS...")
    cursor.execute('''
    CREATE TABLE pos_return_lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        return_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity FLOAT DEFAULT 0.0,
        unit_price FLOAT DEFAULT 0.0,
        subtotal FLOAT DEFAULT 0.0,
        return_reason VARCHAR(64),
        state VARCHAR(20) DEFAULT 'draft',
        notes TEXT
    )
    ''')
    
    print("Creating quality_checks table...")
    cursor.execute('''
    CREATE TABLE quality_checks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(64),
        return_line_id INTEGER NOT NULL,
        quality_state VARCHAR(20) DEFAULT 'pending',
        disposition VARCHAR(20),
        notes TEXT,
        checked_by INTEGER,
        check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    
    # Verify the table structure
    print("\nVerifying table structure...")
    cursor.execute("PRAGMA table_info(pos_return_lines)")
    columns = cursor.fetchall()
    print("\npos_return_lines columns:")
    for col in columns:
        col_id, col_name, col_type, not_null, default_val, pk = col
        print(f"  - {col_name} ({col_type}), PK: {pk}, NOT NULL: {not_null}, DEFAULT: {default_val}")
    
    conn.close()
    print("\nDatabase completely recreated with proper structure!")
    print("Now update the model to match EXACTLY this database structure")

if __name__ == "__main__":
    final_database_fix()
