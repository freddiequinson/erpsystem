from app import create_app, db
from modules.inventory.models import Product
from modules.auth.models import Branch
from modules.pos.models import POSOrder, POSReturn
from sqlalchemy import func
from datetime import datetime, timedelta

app = create_app()
with app.app_context():
    # Get Main Branch
    main_branch = Branch.query.filter_by(name='Main Branch').first()
    if main_branch:
        print(f"Main Branch ID: {main_branch.id}")
    else:
        print("Main Branch not found!")
        
    # Count products
    total_products = Product.query.count()
    print(f"Total products in database: {total_products}")
    
    # Count active products
    active_products = Product.query.filter_by(is_active=True).count()
    print(f"Active products: {active_products}")
    
    # Count products by branch
    if main_branch:
        branch_products = Product.query.filter_by(branch_id=main_branch.id).count()
        print(f"Products in Main Branch: {branch_products}")
        
        active_branch_products = Product.query.filter_by(branch_id=main_branch.id, is_active=True).count()
        print(f"Active products in Main Branch: {active_branch_products}")
    
    # Count orders
    total_orders = POSOrder.query.count()
    print(f"Total orders: {total_orders}")
    
    # Count paid orders
    paid_orders = POSOrder.query.filter_by(state='paid').count()
    print(f"Paid orders: {paid_orders}")
    
    # Count returns
    total_returns = POSReturn.query.count()
    print(f"Total returns: {total_returns}")
    
    # Calculate today's sales
    today = datetime.utcnow().date()
    today_sales = POSOrder.query.filter(
        func.date(POSOrder.order_date) == today,
        POSOrder.state == 'paid'
    ).with_entities(func.sum(POSOrder.total_amount)).scalar() or 0
    
    print(f"Today's sales: {today_sales}")
    
    # Calculate weekly sales
    week_ago = today - timedelta(days=7)
    week_sales = POSOrder.query.filter(
        POSOrder.order_date >= week_ago,
        POSOrder.state == 'paid'
    ).with_entities(func.sum(POSOrder.total_amount)).scalar() or 0
    
    print(f"Weekly sales: {week_sales}")
    
    # Debug the dashboard query directly
    print("\nDebugging dashboard query:")
    
    # Simulate the dashboard query for products
    product_count = Product.query.count()
    print(f"Dashboard product count (all): {product_count}")
    
    # Check if branch filtering is working
    if main_branch:
        branch_product_count = Product.query.filter_by(branch_id=main_branch.id).count()
        print(f"Dashboard product count (branch filtered): {branch_product_count}")
        
    # List a few products to verify they exist
    print("\nSample products:")
    sample_products = Product.query.limit(5).all()
    for product in sample_products:
        print(f"ID: {product.id}, Name: {product.name}, Branch ID: {product.branch_id}, Active: {product.is_active}")
