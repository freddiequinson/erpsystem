import sqlite3
import os
import shutil
import time

def remove_notes_column():
    """Remove the notes column from pos_return_lines table"""
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
    
    # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
    print("Recreating pos_return_lines table without notes column...")
    
    # Create a new table without the notes column
    cursor.execute('''
    CREATE TABLE pos_return_lines_new (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        return_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity FLOAT DEFAULT 0.0,
        unit_price FLOAT DEFAULT 0.0,
        subtotal FLOAT DEFAULT 0.0,
        return_reason VARCHAR(64),
        state VARCHAR(20) DEFAULT 'draft'
    )
    ''')
    
    # Copy data from old table to new table
    try:
        cursor.execute('''
        INSERT INTO pos_return_lines_new (id, return_id, product_id, quantity, unit_price, subtotal, return_reason, state)
        SELECT id, return_id, product_id, quantity, unit_price, subtotal, return_reason, state FROM pos_return_lines
        ''')
        print("Data copied successfully")
    except sqlite3.OperationalError as e:
        print(f"Error copying data: {e}")
    
    # Drop the old table
    cursor.execute("DROP TABLE pos_return_lines")
    
    # Rename the new table to the original name
    cursor.execute("ALTER TABLE pos_return_lines_new RENAME TO pos_return_lines")
    
    conn.commit()
    
    # Verify the table structure
    print("\nVerifying new table structure...")
    cursor.execute("PRAGMA table_info(pos_return_lines)")
    columns = cursor.fetchall()
    print("\npos_return_lines columns:")
    for col in columns:
        col_id, col_name, col_type, not_null, default_val, pk = col
        print(f"  - {col_name} ({col_type}), PK: {pk}, NOT NULL: {not_null}, DEFAULT: {default_val}")
    
    conn.close()
    print("\nNotes column removed successfully!")

if __name__ == "__main__":
    remove_notes_column()
