import sqlite3
from app import db, create_app

def add_employee_id_column():
    """Add employee_id column to pos_orders table"""
    
    # Get the database URI from the app config
    app = create_app()
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # First, let's check what tables exist in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables in the database:", [table[0] for table in tables])
        
        # Find the POS orders table (it might have a different name)
        pos_table_name = None
        for table in tables:
            table_name = table[0]
            if 'pos' in table_name.lower() and 'order' in table_name.lower():
                # Check the structure of this table
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                column_names = [column[1] for column in columns]
                print(f"Found potential POS orders table: {table_name}")
                print(f"Columns: {column_names}")
                
                # Check if this table has typical order columns
                if 'total_amount' in column_names or 'order_date' in column_names:
                    pos_table_name = table_name
                    break
        
        if not pos_table_name:
            print("Could not find the POS orders table. Please check the database structure.")
            return
        
        print(f"Using table: {pos_table_name}")
        
        # Check if the column already exists
        cursor.execute(f"PRAGMA table_info({pos_table_name})")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'employee_id' not in column_names:
            # Add the employee_id column
            cursor.execute(f"ALTER TABLE {pos_table_name} ADD COLUMN employee_id INTEGER")
            print(f"Added employee_id column to {pos_table_name} table")
            
            conn.commit()
            print("Database updated successfully")
        else:
            print(f"employee_id column already exists in {pos_table_name} table")
    
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    add_employee_id_column()
