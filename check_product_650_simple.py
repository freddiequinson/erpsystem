from app import create_app, db
from modules.pos.models import POSOrderLine, Product, POSOrder
from flask import Flask

# Create the app and application context
app = create_app()
with app.app_context():
    print("Checking product 650...")
    
    # Check product 650
    product = Product.query.get(650)
    if product:
        print(f"Product 650: {product.name}")
        print(f"Current stock: {product.stock_quantity}")
    else:
        print("Product 650 not found")
    
    # Find all order lines for product 650
    order_lines = POSOrderLine.query.filter_by(product_id=650).all()
    print(f"\nFound {len(order_lines)} order lines for product 650")
    
    for line in order_lines:
        order = POSOrder.query.get(line.order_id)
        print(f"\nOrder Line ID: {line.id}")
        print(f"Order ID: {line.order_id}")
        print(f"Order Name: {order.name if order else 'Unknown'}")
        print(f"Quantity: {line.quantity}")
        print(f"Returned quantity: {line.returned_quantity}")
        print(f"Returnable quantity: {line.returnable_quantity}")
