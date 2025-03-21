import sqlite3
import os

def run_migration():
    """Add returned_quantity column to pos_order_lines table"""
    # Database path that contains the pos_order_lines table
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'erp_system.db')
    
    if os.path.exists(db_path):
        print(f"\nMigrating database at: {db_path}")
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Check if the pos_order_lines table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pos_order_lines';")
            if not cursor.fetchone():
                print("Table pos_order_lines does not exist in this database.")
                return
            
            # Check if the column already exists in pos_order_lines
            cursor.execute("PRAGMA table_info(pos_order_lines)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'returned_quantity' not in columns:
                print("Adding returned_quantity column to pos_order_lines table...")
                cursor.execute('''
                    ALTER TABLE pos_order_lines
                    ADD COLUMN returned_quantity FLOAT DEFAULT 0.0
                ''')
                print("Column added successfully.")
            else:
                print("Column returned_quantity already exists in pos_order_lines table.")
            
            # Commit the changes
            conn.commit()
            print(f"Migration of {db_path} completed successfully.")
            
        except Exception as e:
            # Rollback in case of error
            conn.rollback()
            print(f"Error during migration of {db_path}: {str(e)}")
            
        finally:
            # Close the connection
            conn.close()
    else:
        print(f"\nDatabase not found: {db_path}")

if __name__ == "__main__":
    run_migration()
