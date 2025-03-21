import sqlite3
import os

def add_missing_columns():
    # Path to the SQLite database
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'database.db')
    
    # Connect to the database
    print(f"Connecting to database at {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if is_active column exists in stock_locations table
    cursor.execute("PRAGMA table_info(stock_locations)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Add is_active column if it doesn't exist
    if 'is_active' not in columns:
        print("Adding is_active column to stock_locations table...")
        cursor.execute("ALTER TABLE stock_locations ADD COLUMN is_active BOOLEAN DEFAULT 1")
        conn.commit()
        print("Column added successfully.")
    else:
        print("is_active column already exists in stock_locations table.")
    
    # Check if code column exists in stock_locations table
    if 'code' not in columns:
        print("Adding code column to stock_locations table...")
        cursor.execute("ALTER TABLE stock_locations ADD COLUMN code VARCHAR(10) DEFAULT NULL")
        conn.commit()
        print("Column added successfully.")
    else:
        print("code column already exists in stock_locations table.")
    
    # Close the connection
    conn.close()
    print("Database update completed.")

if __name__ == "__main__":
    add_missing_columns()
