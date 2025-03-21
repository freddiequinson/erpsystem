import os
import sqlite3

# Get the correct database path from the config
DB_PATH = 'erp_system.db'

# SQL statements to create the returns management tables
CREATE_POS_RETURNS_TABLE = '''
CREATE TABLE IF NOT EXISTS pos_returns (
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
);
'''

CREATE_POS_RETURN_LINES_TABLE = '''
CREATE TABLE IF NOT EXISTS pos_return_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    return_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity FLOAT DEFAULT 0.0,
    unit_price FLOAT DEFAULT 0.0,
    subtotal FLOAT DEFAULT 0.0,
    return_reason VARCHAR(64),
    state VARCHAR(20) DEFAULT 'draft',
    FOREIGN KEY (return_id) REFERENCES pos_returns (id),
    FOREIGN KEY (product_id) REFERENCES products (id)
);
'''

CREATE_QUALITY_CHECKS_TABLE = '''
CREATE TABLE IF NOT EXISTS quality_checks (
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
);
'''

def create_returns_tables():
    """Create the necessary tables for the returns management system."""
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create the tables
        cursor.execute(CREATE_POS_RETURNS_TABLE)
        cursor.execute(CREATE_POS_RETURN_LINES_TABLE)
        cursor.execute(CREATE_QUALITY_CHECKS_TABLE)
        
        # Commit the changes
        conn.commit()
        print("Returns management tables created successfully!")
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        # Close the connection
        if conn:
            conn.close()

if __name__ == "__main__":
    create_returns_tables()
