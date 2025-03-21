import sqlite3
import os

# Connect to the database
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'erp_system.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if the table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pos_receipt_settings'")
if cursor.fetchone():
    print("Found pos_receipt_settings table, backing up existing data...")
    
    # Get existing data
    cursor.execute("SELECT id, header_text, footer_text, show_logo, show_cashier, show_tax_details FROM pos_receipt_settings")
    existing_data = cursor.fetchall()
    
    # Drop the existing table
    cursor.execute("DROP TABLE pos_receipt_settings")
    print("Dropped existing table.")

# Create the table with all columns
cursor.execute("""
CREATE TABLE pos_receipt_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    header_text TEXT,
    footer_text TEXT,
    logo_path TEXT,
    show_logo BOOLEAN DEFAULT 1,
    show_cashier BOOLEAN DEFAULT 1,
    show_tax_details BOOLEAN DEFAULT 1,
    show_barcode BOOLEAN DEFAULT 1,
    show_qr_code BOOLEAN DEFAULT 1,
    show_customer BOOLEAN DEFAULT 1
)
""")
print("Created pos_receipt_settings table with all columns.")

# Restore data if it existed
if 'existing_data' in locals():
    for row in existing_data:
        cursor.execute("""
        INSERT INTO pos_receipt_settings 
        (id, header_text, footer_text, show_logo, show_cashier, show_tax_details, show_barcode, show_qr_code, show_customer) 
        VALUES (?, ?, ?, ?, ?, ?, 1, 1, 1)
        """, row)
    print(f"Restored {len(existing_data)} rows of data.")
else:
    # Insert default row if no data existed
    cursor.execute("""
    INSERT INTO pos_receipt_settings 
    (header_text, footer_text, show_logo, show_cashier, show_tax_details, show_barcode, show_qr_code, show_customer) 
    VALUES ('Thank you for shopping with us!', 'Please come again!', 1, 1, 1, 1, 1, 1)
    """)
    print("Inserted default settings row.")

# Commit changes and close connection
conn.commit()
conn.close()
print("Receipt settings table reset successfully!")
