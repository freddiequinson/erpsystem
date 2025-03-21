import sqlite3
import os

def inspect_database():
    """Inspect the actual database structure"""
    db_path = 'erp_system.db'
    
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # First, let's check all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Found {len(tables)} tables in the database:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Now inspect pos_return_lines in detail
    print("\nExamining pos_return_lines table:")
    try:
        cursor.execute("PRAGMA table_info(pos_return_lines)")
        columns = cursor.fetchall()
        if columns:
            print("pos_return_lines columns:")
            for col in columns:
                col_id, col_name, col_type, not_null, default_val, pk = col
                print(f"  - {col_name} ({col_type}), PK: {pk}, NOT NULL: {not_null}, DEFAULT: {default_val}")
        else:
            print("Table exists but has no columns defined!")
            
        # Try checking if the table actually exists
        try:
            cursor.execute("SELECT * FROM pos_return_lines LIMIT 1")
            print("Table exists and can be queried")
        except sqlite3.OperationalError as e:
            print(f"Error querying table: {e}")
            
    except sqlite3.OperationalError as e:
        print(f"Error inspecting table: {e}")
    
    conn.close()
    print("\nDatabase inspection complete!")

if __name__ == "__main__":
    inspect_database()
