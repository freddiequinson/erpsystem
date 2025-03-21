import sqlite3
import os
import glob

def find_and_fix_stock_locations():
    """Find the database with stock_locations table and fix missing columns"""
    print("Searching for database with stock_locations table...")
    
    # Get all .db files in current directory and instance subdirectory
    db_files = glob.glob('*.db') + glob.glob('instance/*.db')
    
    for db_file in db_files:
        try:
            print(f"\nChecking {db_file}...")
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Check if stock_locations table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stock_locations'")
            if cursor.fetchone():
                print(f"✓ Found stock_locations table in {db_file}")
                
                # Check columns
                cursor.execute("PRAGMA table_info(stock_locations)")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                print("Columns found:")
                for col in columns:
                    print(f"  - {col[1]} ({col[2]})")
                
                # Add missing columns
                if 'is_active' not in column_names:
                    print("\nAdding is_active column...")
                    cursor.execute("ALTER TABLE stock_locations ADD COLUMN is_active BOOLEAN DEFAULT 1")
                    conn.commit()
                    print("✓ is_active column added successfully")
                
                if 'code' not in column_names:
                    print("\nAdding code column...")
                    cursor.execute("ALTER TABLE stock_locations ADD COLUMN code VARCHAR(10) DEFAULT NULL")
                    conn.commit()
                    print("✓ code column added successfully")
                
                print(f"\n✓ Database {db_file} updated successfully")
                
            conn.close()
        except Exception as e:
            print(f"Error with {db_file}: {str(e)}")
    
    print("\nSearch and fix operation completed")

if __name__ == "__main__":
    find_and_fix_stock_locations()
