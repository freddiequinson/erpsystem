import sqlite3
import os

def find_order_lines_table():
    """Find which database contains the pos_order_lines table"""
    # Get all .db files in the directory and subdirectories
    db_files = []
    for root, dirs, files in os.walk(os.path.dirname(os.path.dirname(__file__))):
        for file in files:
            if file.endswith('.db'):
                db_files.append(os.path.join(root, file))
    
    print(f"Found {len(db_files)} database files.")
    
    # Check each database for the pos_order_lines table
    for db_path in db_files:
        try:
            # Connect to the database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if the pos_order_lines table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pos_order_lines';")
            if cursor.fetchone():
                print(f"\nFound pos_order_lines table in: {db_path}")
                
                # Get column info
                cursor.execute("PRAGMA table_info(pos_order_lines)")
                columns = cursor.fetchall()
                print("Columns:")
                for col in columns:
                    print(f"  - {col[1]} ({col[2]})")
                
                # Check if the returned_quantity column exists
                if 'returned_quantity' not in [col[1] for col in columns]:
                    print("The returned_quantity column does not exist in this table.")
            
            # Close the connection
            conn.close()
            
        except Exception as e:
            print(f"Error checking {db_path}: {str(e)}")

if __name__ == "__main__":
    find_order_lines_table()
