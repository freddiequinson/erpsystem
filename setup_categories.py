from app import create_app, db
from modules.pos.models import POSCategory
from modules.inventory.models import Product

app = create_app()

def setup_categories():
    with app.app_context():
        # Check if categories already exist
        if POSCategory.query.count() > 0:
            print("Categories already exist. Skipping creation.")
            return
            
        # Create categories
        categories = [
            {"name": "Electronics", "sequence": 10},
            {"name": "Clothing", "sequence": 20},
            {"name": "Food & Beverages", "sequence": 30},
            {"name": "Home & Kitchen", "sequence": 40},
            {"name": "Health & Beauty", "sequence": 50},
            {"name": "Sports", "sequence": 60}
        ]
        
        created_categories = {}
        
        for cat_data in categories:
            category = POSCategory(
                name=cat_data["name"],
                sequence=cat_data["sequence"]
            )
            db.session.add(category)
            db.session.flush()  # Get the ID without committing
            created_categories[cat_data["name"]] = category.id
            print(f"Created category: {cat_data['name']} with ID {category.id}")
        
        db.session.commit()
        
        # Assign categories to products
        # Get all products
        products = Product.query.all()
        
        # Assign categories based on product name or other criteria
        for product in products:
            # Simple logic to assign categories based on product name
            # In a real system, you'd have more sophisticated logic
            if product.name.lower().startswith(("phone", "laptop", "tv", "computer")):
                product.category_id = created_categories["Electronics"]
            elif product.name.lower().startswith(("shirt", "pant", "dress", "jacket")):
                product.category_id = created_categories["Clothing"]
            elif product.name.lower().startswith(("food", "drink", "juice", "water")):
                product.category_id = created_categories["Food & Beverages"]
            elif product.name.lower().startswith(("chair", "table", "bed", "sofa")):
                product.category_id = created_categories["Home & Kitchen"]
            elif product.name.lower().startswith(("soap", "cream", "lotion", "shampoo")):
                product.category_id = created_categories["Health & Beauty"]
            elif product.name.lower().startswith(("ball", "bat", "racket", "shoe")):
                product.category_id = created_categories["Sports"]
            else:
                # Assign a random category for products that don't match any criteria
                import random
                category_id = random.choice(list(created_categories.values()))
                product.category_id = category_id
            
            print(f"Assigned product {product.name} to category ID {product.category_id}")
        
        db.session.commit()
        print("Categories assigned to products successfully!")

if __name__ == "__main__":
    setup_categories()
    print("Setup complete!")
