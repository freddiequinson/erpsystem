import sqlite3
import os

def inspect_quality_checks_table():
    """Inspect the quality_checks table structure"""
    db_path = 'erp_system.db'
    
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Examining quality_checks table:")
    try:
        cursor.execute("PRAGMA table_info(quality_checks)")
        columns = cursor.fetchall()
        if columns:
            print("quality_checks columns:")
            for col in columns:
                col_id, col_name, col_type, not_null, default_val, pk = col
                print(f"  - {col_name} ({col_type}), PK: {pk}, NOT NULL: {not_null}, DEFAULT: {default_val}")
        else:
            print("Table exists but has no columns defined!")
    except sqlite3.OperationalError as e:
        print(f"Error inspecting table: {e}")
    
    conn.close()
    print("\nInspection complete!")

if __name__ == "__main__":
    inspect_quality_checks_table()
