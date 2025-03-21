import sqlite3
import os

# Connect to the database
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'erp_system.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if the table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pos_receipt_settings'")
if cursor.fetchone():
    print("Found pos_receipt_settings table, checking for company fields...")
    
    # Check if company_name column exists
    cursor.execute("PRAGMA table_info(pos_receipt_settings)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Add company_name column if it doesn't exist
    if 'company_name' not in columns:
        cursor.execute("ALTER TABLE pos_receipt_settings ADD COLUMN company_name TEXT DEFAULT 'YOUR COMPANY NAME'")
        print("Added company_name column")
    
    # Add company_address column if it doesn't exist
    if 'company_address' not in columns:
        cursor.execute("ALTER TABLE pos_receipt_settings ADD COLUMN company_address TEXT DEFAULT '123 Main Street, Accra, Ghana'")
        print("Added company_address column")
    
    # Add company_phone column if it doesn't exist
    if 'company_phone' not in columns:
        cursor.execute("ALTER TABLE pos_receipt_settings ADD COLUMN company_phone TEXT DEFAULT '+233 123 456 789'")
        print("Added company_phone column")
    
    # Commit changes
    conn.commit()
    print("Database updated successfully!")
else:
    print("pos_receipt_settings table not found!")

# Close connection
conn.close()
