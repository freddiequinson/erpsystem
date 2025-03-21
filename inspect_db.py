import sqlite3
import os

def inspect_database():
    """Inspect the database schema and print table information"""
    db_path = 'erp_system.db'
    
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("=== Database Tables ===")
    for table in tables:
        table_name = table[0]
        print(f"\nTable: {table_name}")
        
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        print("Columns:")
        for col in columns:
            col_id, col_name, col_type, not_null, default_val, pk = col
            print(f"  - {col_name} ({col_type}), PK: {pk}, NOT NULL: {not_null}, DEFAULT: {default_val}")
    
    conn.close()

if __name__ == "__main__":
    inspect_database()
