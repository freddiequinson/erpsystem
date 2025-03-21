from app import create_app
from modules.inventory.models import StockLocation, StockMove, Product

app = create_app()

with app.app_context():
    print("Stock Locations:")
    for loc in StockLocation.query.all():
        print(f"ID: {loc.id}, Name: {loc.name}, Type: {loc.location_type}")
    
    print("\nStock Moves:")
    for move in StockMove.query.all():
        print(f"ID: {move.id}, Product: {move.product.name}, Quantity: {move.quantity}, State: {move.state}")
        print(f"  Source: {move.source_location.name} ({move.source_location.location_type})")
        print(f"  Destination: {move.destination_location.name} ({move.destination_location.location_type})")
    
    print("\nProducts with Stock:")
    for product in Product.query.all():
        print(f"ID: {product.id}, Name: {product.name}, Available Quantity: {product.available_quantity}")
