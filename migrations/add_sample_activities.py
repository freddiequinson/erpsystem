"""
Migration script to add sample activities to the activities table
"""
import sqlite3
import os
from datetime import datetime, timedelta

def run_migration():
    """Add sample activities to the activities table"""
    print("Adding sample activities...")
    
    # Connect to the database
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance', 'erp.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if there are any activities
    cursor.execute("SELECT COUNT(*) FROM activities")
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Current time for timestamps
        now = datetime.utcnow()
        
        # Sample activities
        activities = [
            (
                "New product added", 
                "Added 'Premium Coffee Beans' to inventory", 
                "Admin", 
                (now - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
                "inventory"
            ),
            (
                "Sales report generated", 
                "Monthly sales report for March 2025", 
                "Manager", 
                (now - timedelta(hours=5)).strftime('%Y-%m-%d %H:%M:%S'),
                "report"
            ),
            (
                "Return processed", 
                "Processed return #RTN-2025-0042 for defective item", 
                "Sales Rep", 
                (now - timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S'),
                "return"
            ),
            (
                "Quality check completed", 
                "Completed quality inspection for returned items", 
                "Quality Inspector", 
                (now - timedelta(hours=12)).strftime('%Y-%m-%d %H:%M:%S'),
                "quality"
            ),
            (
                "New employee added", 
                "Added John Doe to the Sales department", 
                "HR Manager", 
                (now - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S'),
                "employee"
            )
        ]
        
        # Insert sample activities
        cursor.executemany(
            "INSERT INTO activities (description, details, user, timestamp, activity_type) VALUES (?, ?, ?, ?, ?)",
            activities
        )
        
        # Commit the changes
        conn.commit()
        print(f"Added {len(activities)} sample activities")
    else:
        print(f"Found {count} existing activities, no sample data added")
    
    # Close the connection
    conn.close()
    
    print("Sample activities migration completed!")
    return True

if __name__ == "__main__":
    run_migration()
