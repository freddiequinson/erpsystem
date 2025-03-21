import sqlite3
import os
import sys
from pathlib import Path

def run_migration():
    """Find all SQLite databases and add the required columns to all relevant tables"""
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Find all SQLite database files in the project
    db_files = []
    for root, dirs, files in os.walk(project_root):
        for file in files:
            if file.endswith('.db'):
                db_files.append(os.path.join(root, file))
    
    print(f"Found {len(db_files)} database files.")
    
    # Track which databases were modified
    modified_dbs = []
    
    # Process each database
    for db_path in db_files:
        print(f"\nChecking database: {db_path}")
        
        try:
            # Connect to the database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all tables in the database
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [table[0] for table in cursor.fetchall()]
            
            db_modified = False
            
            # Check for pos_return_lines table
            if 'pos_return_lines' in tables:
                print(f"Found pos_return_lines table in {db_path}")
                
                # Check if original_order_line_id column exists
                cursor.execute("PRAGMA table_info(pos_return_lines)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'original_order_line_id' not in columns:
                    print("Adding original_order_line_id column to pos_return_lines table...")
                    cursor.execute('''
                        ALTER TABLE pos_return_lines
                        ADD COLUMN original_order_line_id INTEGER
                    ''')
                    print("Column added successfully.")
                    db_modified = True
                else:
                    print("Column original_order_line_id already exists in pos_return_lines table.")
            
            # Check for pos_order_lines table
            if 'pos_order_lines' in tables:
                print(f"Found pos_order_lines table in {db_path}")
                
                # Check if returned_quantity column exists
                cursor.execute("PRAGMA table_info(pos_order_lines)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'returned_quantity' not in columns:
                    print("Adding returned_quantity column to pos_order_lines table...")
                    cursor.execute('''
                        ALTER TABLE pos_order_lines
                        ADD COLUMN returned_quantity FLOAT DEFAULT 0.0
                    ''')
                    print("Column added successfully.")
                    db_modified = True
                else:
                    print("Column returned_quantity already exists in pos_order_lines table.")
            
            # Commit changes if any modifications were made
            if db_modified:
                conn.commit()
                modified_dbs.append(db_path)
                print(f"Database {db_path} was modified.")
            else:
                print(f"No changes needed for {db_path}.")
            
        except Exception as e:
            print(f"Error processing {db_path}: {str(e)}")
        finally:
            # Close the connection
            if 'conn' in locals():
                conn.close()
    
    print("\nMigration summary:")
    if modified_dbs:
        print(f"Modified {len(modified_dbs)} databases:")
        for db in modified_dbs:
            print(f"  - {db}")
    else:
        print("No databases were modified.")

if __name__ == "__main__":
    run_migration()
