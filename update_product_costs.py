from app import create_app
from modules.inventory.models import Product
from app import db
import random

app = create_app()

with app.app_context():
    # Get products with available quantity > 0
    products = [p for p in Product.query.all() if p.available_quantity > 0]
    print(f"Found {len(products)} products with inventory")
    
    # Update cost prices for these products
    count = 0
    for product in products:
        # Set a random cost price between 10 and 500 GHC
        product.cost_price = round(random.uniform(10, 500), 2)
        count += 1
        
    # Commit the changes
    db.session.commit()
    print(f"Updated cost prices for {count} products")
    
    # Verify the update
    total_value = sum(p.available_quantity * p.cost_price for p in products)
    print(f"New total inventory value: GHC {total_value:.2f}")
