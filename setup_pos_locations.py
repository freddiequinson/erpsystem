from app import create_app
from extensions import db
from modules.inventory.models import StockLocation, Warehouse

def setup_pos_locations():
    """Set up the necessary stock locations for the POS system"""
    app = create_app()
    
    with app.app_context():
        # Check if we already have the required locations
        shop_location = StockLocation.query.filter_by(code='SHOP').first()
        customer_location = StockLocation.query.filter_by(location_type='customer').first()
        
        if not shop_location:
            print("Creating SHOP location...")
            # First check if we have a warehouse
            warehouse = Warehouse.query.first()
            if not warehouse:
                # Create a default warehouse
                warehouse = Warehouse(name='Main Warehouse', code='WH01', address='Main Street')
                db.session.add(warehouse)
                db.session.commit()
                print(f"Created warehouse: {warehouse.name}")
            
            # Create the SHOP location
            shop_location = StockLocation(
                name='Shop Floor',
                code='SHOP',
                warehouse_id=warehouse.id,
                location_type='internal',
            )
            db.session.add(shop_location)
            db.session.commit()
            print(f"Created shop location: {shop_location.name}")
        else:
            print(f"Shop location already exists: {shop_location.name}")
        
        if not customer_location:
            print("Creating Customer location...")
            # Create the Customer location
            customer_location = StockLocation(
                name='Customers',
                code='CUST',
                location_type='customer',
            )
            db.session.add(customer_location)
            db.session.commit()
            print(f"Created customer location: {customer_location.name}")
        else:
            print(f"Customer location already exists: {customer_location.name}")
        
        # List all locations
        print("\nAvailable Stock Locations:")
        locations = StockLocation.query.all()
        for loc in locations:
            print(f"ID: {loc.id}, Name: {loc.name}, Code: {loc.code}, Type: {loc.location_type}")

if __name__ == "__main__":
    setup_pos_locations()
