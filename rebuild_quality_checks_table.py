import sqlite3
from datetime import datetime
import os

def backup_database(db_path):
    """Create a backup of the database before making changes"""
    backup_path = f"{db_path}_backup_{int(datetime.now().timestamp())}.db"
    with open(db_path, 'rb') as src, open(backup_path, 'wb') as dst:
        dst.write(src.read())
    print(f"Backup created at {backup_path}")
    return backup_path

def main():
    # Database path
    db_path = 'erp_system.db'
    
    # Create backup
    backup_path = backup_database(db_path)
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # First, get all existing quality check data
        cursor.execute("SELECT id, name, return_line_id, quality_state, disposition, notes, checked_by, check_date FROM quality_checks")
        existing_data = cursor.fetchall()
        print(f"Found {len(existing_data)} existing quality checks to migrate")
        
        # Get return line quantities for each check
        return_line_quantities = {}
        for row in existing_data:
            return_line_id = row[2]
            cursor.execute("SELECT quantity FROM pos_return_lines WHERE id = ?", (return_line_id,))
            quantity_result = cursor.fetchone()
            if quantity_result:
                return_line_quantities[row[0]] = quantity_result[0]
            else:
                return_line_quantities[row[0]] = 0.0
        
        # Drop the existing table
        print("Dropping existing quality_checks table...")
        cursor.execute("DROP TABLE IF EXISTS quality_checks")
        
        # Create the table with the correct schema
        print("Creating new quality_checks table with quantity column...")
        cursor.execute("""
        CREATE TABLE quality_checks (
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
        
        # Reinsert the data with quantities
        print("Reinserting quality check data with quantities...")
        for row in existing_data:
            quality_check_id = row[0]
            quantity = return_line_quantities.get(quality_check_id, 0.0)
            
            cursor.execute("""
            INSERT INTO quality_checks (id, name, return_line_id, quality_state, disposition, quantity, notes, checked_by, check_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (row[0], row[1], row[2], row[3], row[4], quantity, row[5], row[6], row[7]))
        
        # Commit changes
        conn.commit()
        print(f"Successfully migrated {len(existing_data)} quality checks with quantity data.")
        print("Migration completed successfully.")
        
    except Exception as e:
        # Rollback in case of error
        conn.rollback()
        print(f"Error during migration: {e}")
        print(f"You can restore from the backup at {backup_path}")
    finally:
        # Close connection
        conn.close()

if __name__ == "__main__":
    main()
