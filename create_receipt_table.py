import sqlite3
import os

# Get the database path - assuming it's in the instance folder
db_path = os.path.join('instance', 'app.db')

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create the pos_receipt_settings table
cursor.execute('''
CREATE TABLE IF NOT EXISTS pos_receipt_settings (
    id INTEGER PRIMARY KEY,
    header_text TEXT,
    footer_text TEXT,
    show_logo BOOLEAN DEFAULT 1,
    show_cashier BOOLEAN DEFAULT 1,
    show_tax_details BOOLEAN DEFAULT 1
)
''')

# Check if there's already a record
cursor.execute('SELECT COUNT(*) FROM pos_receipt_settings')
count = cursor.fetchone()[0]

# If no records exist, insert default settings
if count == 0:
    cursor.execute('''
    INSERT INTO pos_receipt_settings (header_text, footer_text, show_logo, show_cashier, show_tax_details)
    VALUES (?, ?, ?, ?, ?)
    ''', ("Thank you for shopping with us!", "Please come again!", 1, 1, 1))
    print("Default receipt settings added.")
else:
    print("Receipt settings already exist.")

# Commit changes and close connection
conn.commit()
conn.close()

print("Receipt settings table created successfully.")
