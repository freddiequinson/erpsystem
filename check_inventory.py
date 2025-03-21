from app import create_app
from modules.inventory.models import Product, StockMove, StockLocation

app = create_app()

with app.app_context():
    # Check products
    products = Product.query.all()
    print(f"Total products: {len(products)}")
    
    # Check products with cost price > 0
    products_with_cost = Product.query.filter(Product.cost_price > 0).all()
    print(f"Products with cost price > 0: {len(products_with_cost)}")
    
    # Check internal locations
    internal_locations = StockLocation.query.filter_by(location_type='internal').all()
    print(f"Internal locations: {len(internal_locations)}")
    for loc in internal_locations:
        print(f"  - {loc.name} (ID: {loc.id})")
    
    # Check stock moves
    stock_moves = StockMove.query.all()
    print(f"Total stock moves: {len(stock_moves)}")
    
    # Check completed stock moves
    completed_moves = StockMove.query.filter_by(state='done').all()
    print(f"Completed stock moves: {len(completed_moves)}")
    
    # Check products with available quantity
    products_with_qty = [p for p in products if p.available_quantity > 0]
    print(f"Products with available quantity > 0: {len(products_with_qty)}")
    
    # Print details of products with available quantity
    print("\nProducts with inventory:")
    for p in products_with_qty:
        print(f"  - {p.name}: Qty={p.available_quantity}, Cost={p.cost_price}, Value={p.available_quantity * p.cost_price}")
    
    # Print total inventory value
    total_value = sum(p.available_quantity * p.cost_price for p in products if p.available_quantity > 0)
    print(f"\nTotal inventory value: {total_value}")
