import sqlite3
from app import db
from flask import Flask
from config import Config

def add_status_column():
    """Add the missing status column to pos_return_lines table"""
    # Connect to the database
    conn = sqlite3.connect(Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', ''))
    cursor = conn.cursor()
    
    # Check if the column already exists
    cursor.execute("PRAGMA table_info(pos_return_lines)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'status' not in columns:
        print("Adding 'status' column to pos_return_lines table...")
        cursor.execute("ALTER TABLE pos_return_lines ADD COLUMN status VARCHAR(20) DEFAULT 'pending'")
        conn.commit()
        print("Column added successfully!")
    else:
        print("The 'status' column already exists in pos_return_lines table.")
    
    conn.close()

if __name__ == "__main__":
    app = Flask(__name__)
    app.config.from_object(Config)
    
    with app.app_context():
        add_status_column()
