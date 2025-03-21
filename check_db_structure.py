import sqlite3
from app import create_app

def check_db_structure():
    """Check the database structure and print all tables and their columns"""
    
    app = create_app()
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    
    print(f"Database path: {db_path}")
    
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"Found {len(tables)} tables in the database:")
        
        # Print each table and its columns
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print("Columns:")
            for column in columns:
                # Column format: (cid, name, type, notnull, dflt_value, pk)
                print(f"  {column[1]} ({column[2]}), {'NOT NULL' if column[3] else 'NULL'}, {'PK' if column[5] else ''}")
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    check_db_structure()
