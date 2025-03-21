import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app import create_app
from extensions import db
from sqlalchemy import text

def migrate():
    """Add product_type field to products table and set default values"""
    print("Starting migration: Adding product_type field to products table...")
    
    app = create_app()
    with app.app_context():
        # Check if column exists
        conn = db.engine.connect()
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('products')]
        
        if 'product_type' not in columns:
            print("Adding product_type column to products table...")
            conn.execute(text("ALTER TABLE products ADD COLUMN product_type VARCHAR(20) DEFAULT 'stockable'"))
            conn.commit()
            print("Column added successfully!")
        else:
            print("Column product_type already exists. Skipping...")
        
        print("Migration completed successfully!")

if __name__ == "__main__":
    migrate()
