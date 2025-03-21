import sqlite3
from app import db, create_app
from modules.pos.models import POSOrder
from sqlalchemy import inspect

def update_database_schema():
    """Update the database schema to match the current models"""
    
    app = create_app()
    with app.app_context():
        # Get the database URI
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Check if the pos_orders table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pos_orders';")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                print("The pos_orders table doesn't exist. Creating it...")
                # Create the table using SQLAlchemy's create_all
                inspector = inspect(db.engine)
                if not inspector.has_table('pos_orders'):
                    POSOrder.__table__.create(db.engine)
                    print("Created pos_orders table")
            else:
                # Check if the employee_id column exists
                cursor.execute("PRAGMA table_info(pos_orders)")
                columns = cursor.fetchall()
                column_names = [column[1] for column in columns]
                
                if 'employee_id' not in column_names:
                    print("Adding employee_id column to pos_orders table")
                    cursor.execute("ALTER TABLE pos_orders ADD COLUMN employee_id INTEGER")
                    conn.commit()
                    print("Added employee_id column successfully")
                else:
                    print("employee_id column already exists in pos_orders table")
            
            # Print the current structure of the pos_orders table
            cursor.execute("PRAGMA table_info(pos_orders)")
            columns = cursor.fetchall()
            print("\nCurrent structure of pos_orders table:")
            for column in columns:
                print(f"  {column[1]} ({column[2]})")
            
        except Exception as e:
            conn.rollback()
            print(f"Error: {e}")
        
        finally:
            conn.close()

if __name__ == "__main__":
    update_database_schema()
