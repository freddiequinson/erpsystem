from flask import Flask
from extensions import db
from modules.auth.models import User, Role, UserRole, Branch
from modules.inventory.models import Product, StockLocation, StockMove, Warehouse

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///odoo_clone.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    # Create all tables
    db.create_all()
    
    # Check if branches exist
    branches = Branch.query.all()
    if not branches:
        print("Creating branches...")
        main_branch = Branch(name='Main Branch', location='Headquarters', address='123 Main St', is_active=True)
        branch1 = Branch(name='Branch1', location='Downtown', address='456 First Ave', is_active=True)
        db.session.add(main_branch)
        db.session.add(branch1)
        db.session.commit()
        print(f"Created Main Branch (ID: {main_branch.id}) and Branch1 (ID: {branch1.id})")
    else:
        print(f"Found {len(branches)} existing branches")
        for branch in branches:
            print(f"ID: {branch.id}, Name: {branch.name}")
    
    # Check if warehouses exist
    warehouses = Warehouse.query.all()
    if not warehouses:
        print("\nCreating warehouse...")
        main_warehouse = Warehouse(name='Main Warehouse', code='WH01', address='123 Main St')
        db.session.add(main_warehouse)
        db.session.commit()
        print(f"Created Main Warehouse (ID: {main_warehouse.id})")
    else:
        print(f"\nFound {len(warehouses)} existing warehouses")
        for wh in warehouses:
            print(f"ID: {wh.id}, Name: {wh.name}")
    
    # Get branch and warehouse IDs for creating locations
    main_branch = Branch.query.filter_by(name='Main Branch').first()
    branch1 = Branch.query.filter_by(name='Branch1').first()
    main_warehouse = Warehouse.query.filter_by(code='WH01').first()
    
    if main_branch and branch1 and main_warehouse:
        # Check if stock locations exist
        locations = StockLocation.query.all()
        if not locations:
            print("\nCreating stock locations...")
            
            # Create Main Branch locations
            stock = StockLocation(name='Stock', location_type='internal', warehouse_id=main_warehouse.id, branch_id=main_branch.id)
            suppliers = StockLocation(name='Suppliers', location_type='supplier', warehouse_id=main_warehouse.id, branch_id=main_branch.id)
            customers = StockLocation(name='Customers', location_type='customer', warehouse_id=main_warehouse.id, branch_id=main_branch.id)
            inventory_loss = StockLocation(name='Inventory Loss', location_type='inventory_loss', warehouse_id=main_warehouse.id, branch_id=main_branch.id)
            production = StockLocation(name='Production', location_type='production', warehouse_id=main_warehouse.id, branch_id=main_branch.id)
            
            # Create Branch1 locations
            branch1_stock = StockLocation(name='Branch1 Stock', location_type='internal', warehouse_id=main_warehouse.id, branch_id=branch1.id)
            branch1_suppliers = StockLocation(name='Branch1 Suppliers', location_type='supplier', warehouse_id=main_warehouse.id, branch_id=branch1.id)
            branch1_customers = StockLocation(name='Branch1 Customers', location_type='customer', warehouse_id=main_warehouse.id, branch_id=branch1.id)
            
            # Add all locations to session
            db.session.add_all([stock, suppliers, customers, inventory_loss, production, branch1_stock, branch1_suppliers, branch1_customers])
            db.session.commit()
            print("Stock locations created successfully!")
        else:
            print(f"\nFound {len(locations)} existing stock locations")
            for loc in locations:
                branch_name = "No Branch"
                if loc.branch_id:
                    branch = Branch.query.get(loc.branch_id)
                    if branch:
                        branch_name = branch.name
                print(f"ID: {loc.id}, Name: {loc.name}, Type: {loc.location_type}, Branch: {branch_name}")
        
        # Check if products exist
        products = Product.query.all()
        if not products:
            print("\nCreating sample products...")
            product1 = Product(name='Product 1', description='Description for Product 1', sku='SKU001', barcode='BARCODE001', cost_price=10.0, sale_price=15.0, is_active=True, branch_id=main_branch.id)
            product2 = Product(name='Product 2', description='Description for Product 2', sku='SKU002', barcode='BARCODE002', cost_price=20.0, sale_price=30.0, is_active=True, branch_id=main_branch.id)
            product3 = Product(name='Product 3', description='Description for Product 3', sku='SKU003', barcode='BARCODE003', cost_price=5.0, sale_price=8.0, is_active=True, branch_id=branch1.id)
            
            db.session.add_all([product1, product2, product3])
            db.session.commit()
            print("Sample products created successfully!")
        else:
            print(f"\nFound {len(products)} existing products")
    else:
        print("\nCouldn't find required branches or warehouse to create locations")

print("\nDatabase setup complete!")
