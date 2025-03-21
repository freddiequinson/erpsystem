import sqlite3
from datetime import datetime

# Connect to the database
conn = sqlite3.connect('erp_system.db')
cursor = conn.cursor()

# Check if the quantity column already exists
cursor.execute("PRAGMA table_info(quality_checks)")
columns = cursor.fetchall()
column_names = [column[1] for column in columns]

if 'quantity' not in column_names:
    print("Adding quantity column to quality_checks table...")
    cursor.execute("ALTER TABLE quality_checks ADD COLUMN quantity REAL DEFAULT 0.0")
    
    # Update existing records to set quantity equal to the return line quantity
    cursor.execute("""
    UPDATE quality_checks
    SET quantity = (
        SELECT quantity 
        FROM pos_return_lines 
        WHERE pos_return_lines.id = quality_checks.return_line_id
    )
    """)
    
    print("Column added and existing records updated successfully.")
else:
    print("Quantity column already exists in quality_checks table.")

# Commit changes and close connection
conn.commit()
conn.close()

print("Migration completed successfully.")
