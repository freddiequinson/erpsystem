from app import create_app, db
from modules.inventory.models import Product
from modules.auth.models import Branch

app = create_app()
with app.app_context():
    print('Total products:', Product.query.count())
    
    products_with_branch = Product.query.filter(Product.branch_id != None).count()
    print(f'Products with branch_id: {products_with_branch}')
    
    branches = Branch.query.all()
    print("\nBranches:")
    for branch in branches:
        branch_product_count = Product.query.filter_by(branch_id=branch.id).count()
        print(f'Branch: {branch.name} (ID: {branch.id}), Products: {branch_product_count}')
    
    products_without_branch = Product.query.filter(Product.branch_id == None).all()
    print(f"\nProducts without branch assignment: {len(products_without_branch)}")
    for p in products_without_branch[:5]:  
        print(f'Product: {p.name}, SKU: {p.sku}, ID: {p.id}')
    
    if len(products_without_branch) > 5:
        print(f"... and {len(products_without_branch) - 5} more")
    
    print("\nProduct details:")
    products = Product.query.all()
    for p in products[:5]:  
        branch_name = "None"
        if p.branch_id:
            branch = Branch.query.get(p.branch_id)
            if branch:
                branch_name = branch.name
        print(f'Product: {p.name}, SKU: {p.sku}, Branch: {branch_name}, Available: {p.available_quantity}, Active: {p.is_active}')
    
    if len(products) > 5:
        print(f"... and {len(products) - 5} more")

    print("\nLow stock products:")
    all_products = Product.query.filter(Product.is_active == True).all()
    
    low_stock = []
    for product in all_products:
        try:
            qty = product.available_quantity
            if isinstance(qty, (int, float)) and qty < 5:
                low_stock.append(product)
        except Exception as e:
            print(f"Error checking product {product.name}: {str(e)}")
    
    low_stock.sort(key=lambda p: p.available_quantity if isinstance(p.available_quantity, (int, float)) else float('inf'))
    
    if low_stock:
        for p in low_stock:
            print(f'Product: {p.name}, Available: {p.available_quantity}')
    else:
        print("No low stock products found")
