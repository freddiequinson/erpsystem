from app import create_app
from extensions import db
from modules.pos.models import POSCashRegister, POSPaymentMethod
from modules.inventory.models import StockLocation, Warehouse
from flask_login import current_user

def setup_pos_system():
    """Set up the necessary components for the POS system"""
    app = create_app()
    
    with app.app_context():
        # Check if we already have a cash register
        cash_register = POSCashRegister.query.first()
        
        if not cash_register:
            print("Creating Main Cash Register...")
            # Create a cash register
            cash_register = POSCashRegister(
                name='Main Cash Register',
                balance=0.0
            )
            db.session.add(cash_register)
            db.session.commit()
            print(f"Created cash register: {cash_register.name}")
        else:
            print(f"Cash register already exists: {cash_register.name}")
        
        # Check if we have payment methods
        payment_methods = POSPaymentMethod.query.all()
        
        if not payment_methods:
            print("Creating payment methods...")
            # Create payment methods
            payment_methods = [
                POSPaymentMethod(name='Cash', code='cash', is_cash=True, is_active=True),
                POSPaymentMethod(name='Card', code='card', is_cash=False, is_active=True),
                POSPaymentMethod(name='Mobile Money', code='momo', is_cash=False, is_active=True)
            ]
            
            for method in payment_methods:
                db.session.add(method)
            
            db.session.commit()
            print(f"Created {len(payment_methods)} payment methods")
        else:
            print(f"Found {len(payment_methods)} existing payment methods")
        
        # Make sure we have the required stock locations
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
        
        print("\nPOS System setup complete!")

if __name__ == "__main__":
    setup_pos_system()
