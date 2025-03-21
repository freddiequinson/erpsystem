from app import create_app, db
from modules.pos.models import POSOrderLine, Product, POSOrder, POSReturn, POSReturnLine
from flask import Flask

# Create the app and application context
app = create_app()
with app.app_context():
    # Check product 650
    product = Product.query.filter_by(id=650).first()
    
    if product:
        print(f"Product 650: {product.name}")
        print(f"Current stock: {product.stock_quantity}")
        
        # Find all order lines for product 650
        order_lines = POSOrderLine.query.filter_by(product_id=650).all()
        
        print(f"\nFound {len(order_lines)} order lines for product 650")
        
        for line in order_lines:
            order = POSOrder.query.get(line.order_id)
            print(f"\nOrder Line ID: {line.id}")
            print(f"Order ID: {line.order_id}")
            print(f"Order Name: {order.name if order else 'Unknown'}")
            print(f"Order Date: {order.order_date if order else 'Unknown'}")
            print(f"Quantity: {line.quantity}")
            print(f"Returned quantity: {line.returned_quantity}")
            print(f"Returnable quantity: {line.returnable_quantity}")
            
            # Check if there are any returns for this line
            return_lines = POSReturnLine.query.filter_by(original_order_line_id=line.id).all()
            if return_lines:
                print(f"\nFound {len(return_lines)} return lines for this order line:")
                for return_line in return_lines:
                    pos_return = POSReturn.query.get(return_line.return_id)
                    print(f"  Return ID: {return_line.return_id}")
                    print(f"  Return Name: {pos_return.name if pos_return else 'Unknown'}")
                    print(f"  Return Date: {pos_return.return_date if pos_return else 'Unknown'}")
                    print(f"  Return Quantity: {return_line.quantity}")
                    print(f"  Return State: {return_line.state}")
            
            print("-" * 50)
    else:
        print("Product 650 not found")
        
    # Check recent returns for errors
    recent_returns = POSReturn.query.order_by(POSReturn.return_date.desc()).limit(3).all()
    print(f"\nChecking {len(recent_returns)} recent returns:")
    
    for pos_return in recent_returns:
        print(f"\nReturn ID: {pos_return.id}")
        print(f"Return Name: {pos_return.name}")
        print(f"Return Date: {pos_return.return_date}")
        print(f"Return State: {pos_return.state}")
        print(f"Original Order ID: {pos_return.original_order_id}")
        
        for line in pos_return.return_lines:
            product = Product.query.get(line.product_id)
            print(f"  Product: {product.id} - {product.name if product else 'Unknown'}")
            print(f"  Quantity: {line.quantity}")
            print(f"  Original Order Line ID: {line.original_order_line_id}")
            
            if line.original_order_line_id:
                original_line = POSOrderLine.query.get(line.original_order_line_id)
                if original_line:
                    print(f"  Original Quantity: {original_line.quantity}")
                    print(f"  Returned Quantity: {original_line.returned_quantity}")
                    print(f"  Returnable Quantity: {original_line.returnable_quantity}")
                else:
                    print("  Original order line not found")
