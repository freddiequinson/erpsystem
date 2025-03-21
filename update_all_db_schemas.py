import os
import sqlite3
import glob
from datetime import datetime

def backup_database(db_path):
    """Create a backup of the database before making changes"""
    backup_path = f"{db_path}_backup_{int(datetime.now().timestamp())}.db"
    with open(db_path, 'rb') as src, open(backup_path, 'wb') as dst:
        dst.write(src.read())
    print(f"Backup created at {backup_path}")
    return backup_path

def update_database_schema(db_path):
    """Update the schema of a specific database file"""
    if not os.path.exists(db_path):
        print(f"Database {db_path} does not exist. Skipping.")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the quality_checks table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quality_checks'")
        if not cursor.fetchone():
            print(f"Database {db_path} does not have quality_checks table. Skipping.")
            conn.close()
            return False
        
        # Check if the quantity column already exists
        cursor.execute("PRAGMA table_info(quality_checks)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'quantity' not in column_names:
            print(f"Adding quantity column to quality_checks table in {db_path}...")
            
            # Create a backup first
            backup_path = backup_database(db_path)
            
            # Create a new table with the updated schema
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_checks_new (
                id INTEGER PRIMARY KEY,
                name VARCHAR(64),
                return_line_id INTEGER NOT NULL,
                quality_state VARCHAR(20) DEFAULT 'pending',
                disposition VARCHAR(20),
                quantity REAL DEFAULT 0.0,
                notes TEXT,
                checked_by INTEGER,
                check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (return_line_id) REFERENCES pos_return_lines (id),
                FOREIGN KEY (checked_by) REFERENCES users (id)
            )
            """)
            
            # Copy data from the old table to the new one
            cursor.execute("""
            INSERT INTO quality_checks_new (
                id, name, return_line_id, quality_state, disposition, notes, checked_by, check_date
            )
            SELECT id, name, return_line_id, quality_state, disposition, notes, checked_by, check_date
            FROM quality_checks
            """)
            
            # Update the quantity values based on return lines
            cursor.execute("""
            UPDATE quality_checks_new
            SET quantity = (
                SELECT quantity 
                FROM pos_return_lines 
                WHERE pos_return_lines.id = quality_checks_new.return_line_id
            )
            """)
            
            # Drop the old table and rename the new one
            cursor.execute("DROP TABLE quality_checks")
            cursor.execute("ALTER TABLE quality_checks_new RENAME TO quality_checks")
            
            # Commit changes
            conn.commit()
            print(f"Successfully updated schema in {db_path}")
            return True
        else:
            print(f"Quantity column already exists in quality_checks table in {db_path}. No changes needed.")
            return False
    except Exception as e:
        print(f"Error updating {db_path}: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    # Find all database files
    db_files = glob.glob('*.db') + glob.glob('instance/*.db')
    
    # Add specific known database files
    specific_files = ['erp_system.db', 'instance/erp_system.db', 'odoo_clone.db']
    for file in specific_files:
        if file not in db_files and os.path.exists(file):
            db_files.append(file)
    
    print(f"Found {len(db_files)} database files to check")
    
    # Update each database
    updated_count = 0
    for db_file in db_files:
        print(f"\nProcessing {db_file}...")
        if update_database_schema(db_file):
            updated_count += 1
    
    print(f"\nCompleted. Updated {updated_count} database files.")

if __name__ == "__main__":
    main()
