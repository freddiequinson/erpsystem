from flask import Flask
from extensions import db
import sqlite3
import os
from config import config

def recreate_tables():
    # Create a Flask app context
    app = Flask(__name__)
    app.config.from_object(config['default'])
    config['default'].init_app(app)
    db.init_app(app)
    
    with app.app_context():
        # Get database path from config
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        print(f"Connecting to database: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Drop existing tables
        print("Dropping existing tables...")
        cursor.execute('DROP TABLE IF EXISTS quality_checks')
        cursor.execute('DROP TABLE IF EXISTS pos_return_lines')
        cursor.execute('DROP TABLE IF EXISTS pos_returns')
        conn.commit()
        
        # Create tables with correct schema
        print("Creating pos_returns table...")
        cursor.execute('''
            CREATE TABLE pos_returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(64) UNIQUE,
                original_order_id INTEGER,
                customer_name VARCHAR(128),
                customer_phone VARCHAR(64),
                return_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_amount FLOAT DEFAULT 0.0,
                refund_amount FLOAT DEFAULT 0.0,
                return_type VARCHAR(20),
                refund_method VARCHAR(20),
                notes TEXT,
                created_by INTEGER,
                state VARCHAR(20) DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (original_order_id) REFERENCES pos_orders (id),
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        print("Creating pos_return_lines table...")
        cursor.execute('''
            CREATE TABLE pos_return_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                return_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                original_line_id INTEGER,
                quantity FLOAT DEFAULT 0.0,
                unit_price FLOAT DEFAULT 0.0,
                subtotal FLOAT DEFAULT 0.0,
                reason VARCHAR(64),
                state VARCHAR(20) DEFAULT 'draft',
                notes TEXT,
                FOREIGN KEY (return_id) REFERENCES pos_returns (id),
                FOREIGN KEY (product_id) REFERENCES products (id),
                FOREIGN KEY (original_line_id) REFERENCES pos_order_lines (id)
            )
        ''')
        
        print("Creating quality_checks table...")
        cursor.execute('''
            CREATE TABLE quality_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(64) UNIQUE,
                return_line_id INTEGER NOT NULL,
                quality_state VARCHAR(20) DEFAULT 'pending',
                disposition VARCHAR(20),
                notes TEXT,
                checked_by INTEGER,
                check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (return_line_id) REFERENCES pos_return_lines (id),
                FOREIGN KEY (checked_by) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        print("Tables recreated successfully!")

if __name__ == "__main__":
    recreate_tables()
