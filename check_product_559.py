from app import create_app, db
from modules.pos.models import POSOrderLine, Product, POSOrder
from flask import Flask

# Create the app and application context
app = create_app()
with app.app_context():
    print("Checking product 559...")
    
    # Check product 559
    product = Product.query.get(559)
    if product:
        print(f"Product 559: {product.name}")
        print(f"Current stock: {product.stock_quantity}")
    else:
        print("Product 559 not found")
    
    # Find all order lines for product 559
    order_lines = POSOrderLine.query.filter_by(product_id=559).all()
    print(f"\nFound {len(order_lines)} order lines for product 559")
    
    for line in order_lines:
        order = POSOrder.query.get(line.order_id)
        print(f"\nOrder Line ID: {line.id}")
        print(f"Order ID: {line.order_id}")
        print(f"Order Name: {order.name if order else 'Unknown'}")
        print(f"Quantity: {line.quantity}")
        print(f"Returned quantity: {line.returned_quantity}")
        print(f"Returnable quantity: {line.returnable_quantity}")
        
        # Check if this is a recent order
        if order and hasattr(order, 'order_date'):
            print(f"Order Date: {order.order_date}")
            
        # Check if this order was created by a specific employee
        if order and hasattr(order, 'created_by'):
            print(f"Created By: {order.created_by}")
            
        # Print the calculation for returnable_quantity
        print(f"Calculation: max(0, {line.quantity} - {line.returned_quantity}) = {max(0, line.quantity - line.returned_quantity)}")
