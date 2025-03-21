"""
Migration script to create the events table and add sample events
"""
import sqlite3
import os
from datetime import datetime, timedelta

def run_migration():
    """Create the events table and add sample events"""
    print("Creating events table...")
    
    # Connect to the database
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance', 'erp.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create the events table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title VARCHAR(128) NOT NULL,
        description TEXT,
        date TIMESTAMP NOT NULL,
        end_date TIMESTAMP,
        location VARCHAR(128),
        event_type VARCHAR(32),
        created_by VARCHAR(64),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Check if there are any events
    cursor.execute("SELECT COUNT(*) FROM events")
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Current time for reference
        now = datetime.utcnow()
        
        # Sample events - using Ghana-specific events and locations
        events = [
            (
                "Inventory Stocktaking", 
                "Complete physical inventory count for Q2", 
                (now + timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S'),
                (now + timedelta(days=2, hours=4)).strftime('%Y-%m-%d %H:%M:%S'),
                "Main Warehouse",
                "inventory",
                "Warehouse Manager"
            ),
            (
                "Staff Training - POS System", 
                "Training session on new POS features", 
                (now + timedelta(days=5)).strftime('%Y-%m-%d %H:%M:%S'),
                (now + timedelta(days=5, hours=3)).strftime('%Y-%m-%d %H:%M:%S'),
                "Training Room",
                "training",
                "IT Manager"
            ),
            (
                "Monthly Sales Review", 
                "Review of sales performance and targets", 
                (now + timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S'),
                (now + timedelta(days=7, hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
                "Conference Room",
                "meeting",
                "Sales Director"
            ),
            (
                "Supplier Meeting - Accra Goods Ltd", 
                "Negotiation of new supply terms", 
                (now + timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S'),
                (now + timedelta(days=10, hours=1, minutes=30)).strftime('%Y-%m-%d %H:%M:%S'),
                "Executive Boardroom",
                "meeting",
                "Procurement Manager"
            ),
            (
                "Product Launch - Premium Line", 
                "Launch event for new premium product line", 
                (now + timedelta(days=14)).strftime('%Y-%m-%d %H:%M:%S'),
                (now + timedelta(days=14, hours=5)).strftime('%Y-%m-%d %H:%M:%S'),
                "Kempinski Hotel, Accra",
                "marketing",
                "Marketing Director"
            )
        ]
        
        # Insert sample events
        cursor.executemany(
            "INSERT INTO events (title, description, date, end_date, location, event_type, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
            events
        )
        
        # Commit the changes
        conn.commit()
        print(f"Added {len(events)} sample events")
    else:
        print(f"Found {count} existing events, no sample data added")
    
    # Close the connection
    conn.close()
    
    print("Events table creation completed!")
    return True

if __name__ == "__main__":
    run_migration()
