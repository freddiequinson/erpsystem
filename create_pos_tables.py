from app import db, create_app
from modules.pos.models import POSOrder, POSOrderLine, POSSession, POSCashRegister, POSSettings
from sqlalchemy import text

def create_pos_tables():
    """Create the missing POS tables in the database"""
    
    app = create_app()
    with app.app_context():
        # Create the tables
        print("Creating POS tables...")
        
        # Create tables for POS models
        db.create_all()
        
        # Check if stock locations exist
        from modules.inventory.models import StockLocation
        shop_floor = StockLocation.query.filter_by(name='Shop Floor').first()
        customers = StockLocation.query.filter_by(name='Customers').first()
        
        # Create stock locations if they don't exist
        if not shop_floor:
            shop_floor = StockLocation(name='Shop Floor', code='SHOP', is_internal=True)
            db.session.add(shop_floor)
            print("Created Shop Floor location")
        
        if not customers:
            customers = StockLocation(name='Customers', code='CUST', is_internal=False)
            db.session.add(customers)
            print("Created Customers location")
        
        # Create default POS settings if they don't exist
        settings = POSSettings.query.first()
        if not settings:
            settings = POSSettings(
                currency_symbol='₵',
                default_customer_id=None
            )
            db.session.add(settings)
            print("Created default POS settings")
        
        # Commit the changes
        db.session.commit()
        print("POS tables created successfully")
        
        # Verify that the pos_orders table exists
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"Tables in database: {tables}")
        
        if 'pos_orders' in tables:
            print("pos_orders table exists")
            # Check if employee_id column exists
            columns = [col['name'] for col in inspector.get_columns('pos_orders')]
            print(f"Columns in pos_orders: {columns}")
            if 'employee_id' in columns:
                print("employee_id column exists in pos_orders table")
            else:
                print("employee_id column does not exist in pos_orders table")
                # Add employee_id column using raw SQL with the correct SQLAlchemy syntax
                with db.engine.connect() as conn:
                    conn.execute(text('ALTER TABLE pos_orders ADD COLUMN employee_id INTEGER'))
                    conn.commit()
                print("Added employee_id column to pos_orders table")
        else:
            print("pos_orders table does not exist")

if __name__ == "__main__":
    create_pos_tables()
