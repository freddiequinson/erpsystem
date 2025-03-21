"""
Migration script to create the activities table using direct SQL
"""
import sqlite3
import os

def run_migration():
    """Create the activities table using direct SQL"""
    print("Creating activities table...")
    
    # Connect to the database
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance', 'erp.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create the activities table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description VARCHAR(128) NOT NULL,
        details TEXT,
        user VARCHAR(64),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        activity_type VARCHAR(32)
    )
    ''')
    
    # Commit the changes and close the connection
    conn.commit()
    conn.close()
    
    print("Activities table created successfully!")
    return True

if __name__ == "__main__":
    run_migration()
