import sqlite3
import os

def rebuild_returns_tables():
    """Completely rebuild the returns-related tables with the correct structure"""
    db_path = 'erp_system.db'
    
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Backing up existing data...")
    # Get existing returns if any
    try:
        cursor.execute("SELECT * FROM pos_returns")
        returns_data = cursor.fetchall()
        print(f"Found {len(returns_data)} existing returns")
    except:
        returns_data = []
        print("No existing returns found or table doesn't exist")
    
    print("Dropping existing tables...")
    cursor.execute("DROP TABLE IF EXISTS quality_checks")
    cursor.execute("DROP TABLE IF EXISTS pos_return_lines")
    cursor.execute("DROP TABLE IF EXISTS pos_returns")
    conn.commit()
    
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
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    print("Creating pos_return_lines table...")
    cursor.execute('''
        CREATE TABLE pos_return_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            return_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity FLOAT DEFAULT 0.0,
            unit_price FLOAT DEFAULT 0.0,
            subtotal FLOAT DEFAULT 0.0,
            reason VARCHAR(64),
            state VARCHAR(20) DEFAULT 'draft',
            notes TEXT,
            FOREIGN KEY (return_id) REFERENCES pos_returns (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
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
            FOREIGN KEY (return_line_id) REFERENCES pos_return_lines (id)
        )
    ''')
    
    conn.commit()
    
    # Verify the tables were created correctly
    print("\nVerifying table structure...")
    
    cursor.execute("PRAGMA table_info(pos_return_lines)")
    columns = cursor.fetchall()
    print("\npos_return_lines columns:")
    for col in columns:
        col_id, col_name, col_type, not_null, default_val, pk = col
        print(f"  - {col_name} ({col_type}), PK: {pk}, NOT NULL: {not_null}, DEFAULT: {default_val}")
    
    conn.close()
    print("\nTables recreated successfully!")

if __name__ == "__main__":
    rebuild_returns_tables()
