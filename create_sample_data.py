from app import create_app, db
from modules.purchase.models import Supplier, PurchaseOrder, PurchaseOrderLine
from modules.inventory.models import Product, StockLocation, Category, UnitOfMeasure
from datetime import datetime, timedelta

app = create_app()
with app.app_context():
    # Check if we have UOM
    if UnitOfMeasure.query.count() == 0:
        print("Creating basic units of measure...")
        uoms = [
            UnitOfMeasure(name="Unit", code="UNT", category="unit", ratio=1.0),
            UnitOfMeasure(name="Dozen", code="DOZ", category="unit", ratio=12.0),
            UnitOfMeasure(name="Kilogram", code="KG", category="weight", ratio=1.0),
            UnitOfMeasure(name="Gram", code="G", category="weight", ratio=0.001),
            UnitOfMeasure(name="Meter", code="M", category="length", ratio=1.0),
            UnitOfMeasure(name="Centimeter", code="CM", category="length", ratio=0.01),
        ]
        for uom in uoms:
            db.session.add(uom)
        db.session.commit()
        print(f"Created {len(uoms)} units of measure")
    
    # Check if we have categories
    if Category.query.count() == 0:
        print("Creating product categories...")
        categories = [
            Category(name="Electronics", description="Electronic products and components"),
            Category(name="Office Supplies", description="Office stationery and supplies"),
            Category(name="Furniture", description="Office furniture"),
            Category(name="IT Equipment", description="Computer hardware and accessories"),
            Category(name="Raw Materials", description="Raw materials for production"),
        ]
        for category in categories:
            db.session.add(category)
        db.session.commit()
        print(f"Created {len(categories)} product categories")
    
    # Check if we have products
    if Product.query.count() == 0:
        print("Creating sample products...")
        
        # Get UOMs and categories
        unit_uom = UnitOfMeasure.query.filter_by(code="UNT").first()
        kg_uom = UnitOfMeasure.query.filter_by(code="KG").first()
        electronics_category = Category.query.filter_by(name="Electronics").first()
        office_category = Category.query.filter_by(name="Office Supplies").first()
        it_category = Category.query.filter_by(name="IT Equipment").first()
        
        # Create products
        products = [
            Product(
                name="Laptop", 
                description="Business laptop", 
                sku="LAP001", 
                barcode="1234567890123", 
                category_id=it_category.id if it_category else None,
                uom_id=unit_uom.id if unit_uom else None,
                product_type="stockable",
                cost_price=800.0,
                sale_price=1200.0,
                min_stock=5.0,
                max_stock=20.0,
                is_active=True
            ),
            Product(
                name="Desktop Computer", 
                description="Office desktop computer", 
                sku="DSK001", 
                barcode="2234567890123", 
                category_id=it_category.id if it_category else None,
                uom_id=unit_uom.id if unit_uom else None,
                product_type="stockable",
                cost_price=600.0,
                sale_price=900.0,
                min_stock=3.0,
                max_stock=15.0,
                is_active=True
            ),
            Product(
                name="Printer", 
                description="Office laser printer", 
                sku="PRT001", 
                barcode="3234567890123", 
                category_id=it_category.id if it_category else None,
                uom_id=unit_uom.id if unit_uom else None,
                product_type="stockable",
                cost_price=250.0,
                sale_price=400.0,
                min_stock=2.0,
                max_stock=10.0,
                is_active=True
            ),
            Product(
                name="Office Paper", 
                description="A4 office paper, 500 sheets", 
                sku="PAP001", 
                barcode="4234567890123", 
                category_id=office_category.id if office_category else None,
                uom_id=unit_uom.id if unit_uom else None,
                product_type="stockable",
                cost_price=5.0,
                sale_price=8.0,
                min_stock=20.0,
                max_stock=100.0,
                is_active=True
            ),
            Product(
                name="Ballpoint Pen", 
                description="Blue ballpoint pen", 
                sku="PEN001", 
                barcode="5234567890123", 
                category_id=office_category.id if office_category else None,
                uom_id=unit_uom.id if unit_uom else None,
                product_type="stockable",
                cost_price=0.5,
                sale_price=1.0,
                min_stock=50.0,
                max_stock=200.0,
                is_active=True
            ),
        ]
        
        for product in products:
            db.session.add(product)
        
        db.session.commit()
        print(f"Created {len(products)} products")

    # Check if we already have suppliers
    if Supplier.query.count() == 0:
        print("Creating sample suppliers...")
        
        # Create suppliers
        suppliers = [
            Supplier(
                name="ABC Electronics",
                contact_name="John Smith",
                email="john@abcelectronics.com",
                phone="555-123-4567",
                address="123 Main St",
                city="Accra",
                state="Greater Accra",
                zip_code="00233",
                country="Ghana",
                website="www.abcelectronics.com",
                tax_id="TAX12345",
                notes="Reliable supplier for electronic components",
                is_active=True
            ),
            Supplier(
                name="XYZ Office Supplies",
                contact_name="Jane Doe",
                email="jane@xyzoffice.com",
                phone="555-987-6543",
                address="456 Market St",
                city="Kumasi",
                state="Ashanti",
                zip_code="00234",
                country="Ghana",
                website="www.xyzoffice.com",
                tax_id="TAX67890",
                notes="Office supplies and equipment",
                is_active=True
            )
        ]
        
        for supplier in suppliers:
            db.session.add(supplier)
        
        db.session.commit()
        print(f"Created {len(suppliers)} suppliers")
    
    # Check if we have products
    products = Product.query.all()
    if not products:
        print("No products found. Please create products first.")
    else:
        # Check if we already have purchase orders
        if PurchaseOrder.query.count() == 0 and Supplier.query.count() > 0:
            print("Creating sample purchase orders...")
            
            # Get supplier
            supplier = Supplier.query.first()
            
            # Create purchase order
            order = PurchaseOrder(
                name="PO-2025-001",
                supplier_id=supplier.id,
                order_date=datetime.utcnow(),
                expected_date=datetime.utcnow() + timedelta(days=7),
                state="draft",
                notes="Sample purchase order"
            )
            
            db.session.add(order)
            db.session.flush()  # Get the order ID
            
            # Add order lines for the first 3 products
            for i, product in enumerate(products[:3]):
                line = PurchaseOrderLine(
                    order_id=order.id,
                    product_id=product.id,
                    description=product.name,
                    quantity=i+1,
                    unit_price=product.cost_price or 100.0,
                    tax_percent=15.0
                )
                db.session.add(line)
            
            # Create a confirmed order too
            confirmed_order = PurchaseOrder(
                name="PO-2025-002",
                supplier_id=supplier.id,
                order_date=datetime.utcnow() - timedelta(days=1),
                expected_date=datetime.utcnow() + timedelta(days=5),
                state="confirmed",
                notes="Confirmed purchase order"
            )
            
            db.session.add(confirmed_order)
            db.session.flush()  # Get the order ID
            
            # Add order lines for the next 2 products
            for i, product in enumerate(products[3:5] if len(products) >= 5 else products[:2]):
                line = PurchaseOrderLine(
                    order_id=confirmed_order.id,
                    product_id=product.id,
                    description=product.name,
                    quantity=i+2,
                    unit_price=product.cost_price or 150.0,
                    tax_percent=15.0
                )
                db.session.add(line)
            
            # Calculate totals
            order.calculate_totals()
            confirmed_order.calculate_totals()
            
            db.session.commit()
            print(f"Created 2 purchase orders with lines")
            
    # Ensure stock locations exist
    locations = {
        'supplier': 'Supplier Location',
        'internal': 'Stock',
        'inventory_loss': 'Inventory Loss'
    }
    
    for location_type, name in locations.items():
        if not StockLocation.query.filter_by(location_type=location_type, name=name).first():
            print(f"Creating {location_type} location: {name}")
            location = StockLocation(
                name=name,
                location_type=location_type,
                code=location_type.upper()[:5]
            )
            db.session.add(location)
    
    db.session.commit()
    print("Stock locations verified")
