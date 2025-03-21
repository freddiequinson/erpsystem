import sqlite3
import os

def run_migration():
    """Add original_order_line_id column to pos_return_lines table and returned_quantity to pos_order_lines"""
    # List of potential database files
    db_paths = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'odoo_clone.db'),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'erp_system.db')
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"\nMigrating database at: {db_path}")
            
            # Connect to the database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            try:
                # Check if the table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pos_return_lines';")
                if not cursor.fetchone():
                    print("Table pos_return_lines does not exist in this database.")
                    continue
                
                # Check if the column already exists in pos_return_lines
                cursor.execute("PRAGMA table_info(pos_return_lines)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'original_order_line_id' not in columns:
                    print("Adding original_order_line_id column to pos_return_lines table...")
                    cursor.execute('''
                        ALTER TABLE pos_return_lines
                        ADD COLUMN original_order_line_id INTEGER
                    ''')
                    print("Column added successfully.")
                else:
                    print("Column original_order_line_id already exists in pos_return_lines table.")
                    
                # Check if the pos_order_lines table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pos_order_lines';")
                if not cursor.fetchone():
                    print("Table pos_order_lines does not exist in this database.")
                else:
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
    
    print("\nMigration process completed.")

if __name__ == "__main__":
    run_migration()
