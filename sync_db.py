from app import create_app
from extensions import db
from sqlalchemy import text

def sync_database():
    app = create_app('development')
    with app.app_context():
        # Drop and recreate the stock_locations table
        print("Dropping and recreating stock_locations table...")
        db.session.execute(text("DROP TABLE IF EXISTS stock_locations"))
        db.session.commit()
        
        # Create the table using SQLAlchemy's create_all
        print("Creating tables from SQLAlchemy models...")
        db.create_all()
        
        # Create default locations
        from modules.inventory.models import StockLocation, Warehouse
        
        # Check if supplier location exists
        supplier_location = StockLocation.query.filter_by(location_type='supplier').first()
        if not supplier_location:
            print("Creating supplier location...")
            supplier_location = StockLocation(
                name='Supplier',
                code='SUP',
                location_type='supplier'
            )
            db.session.add(supplier_location)
        
        # Check if inventory loss location exists
        inventory_loss_location = StockLocation.query.filter_by(location_type='inventory_loss').first()
        if not inventory_loss_location:
            print("Creating inventory loss location...")
            inventory_loss_location = StockLocation(
                name='Inventory Loss',
                code='INV-LOSS',
                location_type='inventory_loss'
            )
            db.session.add(inventory_loss_location)
        
        # Check if warehouse exists
        warehouse = Warehouse.query.first()
        if not warehouse:
            print("Creating main warehouse...")
            warehouse = Warehouse(
                name='Main Warehouse',
                code='MAIN',
                address='Default Address'
            )
            db.session.add(warehouse)
            db.session.commit()
        
        # Check if internal location exists for this warehouse
        internal_location = StockLocation.query.filter_by(
            warehouse_id=warehouse.id, 
            location_type='internal'
        ).first()
        
        if not internal_location:
            print("Creating internal location for warehouse...")
            internal_location = StockLocation(
                name='Main Stock',
                code='STOCK',
                warehouse_id=warehouse.id,
                location_type='internal'
            )
            db.session.add(internal_location)
        
        db.session.commit()
        print("Database synchronized successfully!")

if __name__ == '__main__':
    sync_database()
