import sqlite3
import os

def check_tables():
    """Check all tables in the database"""
    # List of potential database files
    db_paths = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'odoo.db'),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'odoo_clone.db'),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'erp_system.db')
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"\nChecking database at: {db_path}")
            
            # Connect to the database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            try:
                # Get all table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                print("Tables in the database:")
                for table in tables:
                    print(f"- {table[0]}")
                    
                    # Check if this is the table we're looking for
                    if table[0] in ['pos_return_lines', 'pos_order_lines']:
                        print(f"\nFound target table: {table[0]}")
                        # Get column info
                        cursor.execute(f"PRAGMA table_info({table[0]})")
                        columns = cursor.fetchall()
                        print("Columns:")
                        for col in columns:
                            print(f"  - {col[1]} ({col[2]})")
                
            except Exception as e:
                print(f"Error: {str(e)}")
                
            finally:
                # Close the connection
                conn.close()
        else:
            print(f"\nDatabase not found: {db_path}")

if __name__ == "__main__":
    check_tables()
