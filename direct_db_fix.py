import sqlite3
import os

def fix_database_directly():
    """Directly modify the database structure using raw SQL"""
    db_path = 'erp_system.db'
    
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # First, let's check if the table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pos_return_lines'")
    if cursor.fetchone():
        print("Table pos_return_lines exists, checking columns...")
        
        # Check columns
        cursor.execute("PRAGMA table_info(pos_return_lines)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        print(f"Existing columns: {column_names}")
        
        # Check if 'reason' column exists
        if 'reason' not in column_names:
            print("'reason' column does not exist, adding it...")
            try:
                cursor.execute("ALTER TABLE pos_return_lines ADD COLUMN reason VARCHAR(64)")
                conn.commit()
                print("Added 'reason' column successfully")
            except sqlite3.OperationalError as e:
                print(f"Error adding column: {e}")
    else:
        print("Table pos_return_lines does not exist, creating it...")
        
        # Create the table from scratch
        cursor.execute('''
            CREATE TABLE pos_return_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                return_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity FLOAT DEFAULT 0.0,
                unit_price FLOAT DEFAULT 0.0,
                subtotal FLOAT DEFAULT 0.0,
                reason VARCHAR(64),
                state VARCHAR(20) DEFAULT 'draft',
                notes TEXT,
                FOREIGN KEY (return_id) REFERENCES pos_returns (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        conn.commit()
        print("Created pos_return_lines table with all required columns")
    
    # Verify the table structure after changes
    print("\nVerifying final table structure...")
    cursor.execute("PRAGMA table_info(pos_return_lines)")
    columns = cursor.fetchall()
    print("\npos_return_lines columns:")
    for col in columns:
        col_id, col_name, col_type, not_null, default_val, pk = col
        print(f"  - {col_name} ({col_type}), PK: {pk}, NOT NULL: {not_null}, DEFAULT: {default_val}")
    
    conn.close()
    print("\nDatabase structure updated!")

if __name__ == "__main__":
    fix_database_directly()
