from app import app, db
from modules.pos.models import POSCashRegister
import sqlite3
import os

def add_column_if_not_exists():
    # Get the database path from the app config
    with app.app_context():
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if the column exists
    cursor.execute("PRAGMA table_info(pos_cash_registers)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # If is_active column doesn't exist, add it
    if 'is_active' not in columns:
        print("Adding is_active column to pos_cash_registers table...")
        cursor.execute("ALTER TABLE pos_cash_registers ADD COLUMN is_active BOOLEAN DEFAULT 1")
        conn.commit()
        print("Column added successfully!")
    else:
        print("is_active column already exists in pos_cash_registers table.")
    
    # Close the connection
    conn.close()

if __name__ == '__main__':
    with app.app_context():
        add_column_if_not_exists()
        
        # Set all existing cash registers to active
        cash_registers = POSCashRegister.query.all()
        for register in cash_registers:
            register.is_active = True
        
        db.session.commit()
        print(f"Updated {len(cash_registers)} cash registers to active status.")
