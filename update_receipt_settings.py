import sqlite3
import os

# Connect to the database
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'erp_system.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if the table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pos_receipt_settings'")
if not cursor.fetchone():
    print("The pos_receipt_settings table does not exist.")
    conn.close()
    exit(1)

# Add the new columns if they don't exist
columns_to_add = {
    'logo_path': 'VARCHAR(255)',
    'show_barcode': 'BOOLEAN DEFAULT 1',
    'show_qr_code': 'BOOLEAN DEFAULT 1',
    'show_customer': 'BOOLEAN DEFAULT 1'
}

# Get existing columns
cursor.execute(f"PRAGMA table_info(pos_receipt_settings)")
existing_columns = [column[1] for column in cursor.fetchall()]

# Add columns that don't exist
for column_name, column_type in columns_to_add.items():
    if column_name not in existing_columns:
        print(f"Adding column {column_name} to pos_receipt_settings table...")
        cursor.execute(f"ALTER TABLE pos_receipt_settings ADD COLUMN {column_name} {column_type}")

# Commit changes and close connection
conn.commit()
conn.close()
print("Receipt settings table updated successfully!")
