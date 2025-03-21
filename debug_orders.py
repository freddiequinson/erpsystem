from flask import Flask
from extensions import db
from modules.sales.models import SalesOrder
from modules.pos.models import POSOrder
from datetime import datetime
from config import config
from sqlalchemy import func

# Create the app
app = Flask(__name__)
app.config.from_object(config['default'])
config['default'].init_app(app)
db.init_app(app)

with app.app_context():
    now = datetime.utcnow()
    first_day_of_month = datetime(now.year, now.month, 1)
    
    # Debug the actual query being used in the dashboard
    print("=== DEBUGGING DASHBOARD QUERY ===")
    
    # Check sales orders for current month
    sales_query = db.session.query(SalesOrder).filter(
        SalesOrder.order_date >= first_day_of_month
    )
    
    # Print the SQL query
    print("\nSales Orders Query:")
    print(str(sales_query))
    
    # Execute and print results
    sales_orders = sales_query.all()
    print(f"\nSales Orders this month: {len(sales_orders)}")
    for order in sales_orders:
        print(f"  - Order {order.name}, Date: {order.order_date}, State: {order.state}")
    
    # Check POS orders for current month
    pos_query = db.session.query(POSOrder).filter(
        POSOrder.order_date >= first_day_of_month
    )
    
    # Print the SQL query
    print("\nPOS Orders Query:")
    print(str(pos_query))
    
    # Execute and print results
    pos_orders = pos_query.all()
    print(f"\nPOS Orders this month: {len(pos_orders)}")
    for order in pos_orders:
        print(f"  - Order {order.name}, Date: {order.order_date}, State: {order.state}")
    
    # Show total
    total_orders = len(sales_orders) + len(pos_orders)
    print(f"\nTotal Orders: {total_orders}")
    
    # Check if the order_date field might be None or have timezone issues
    print("\n=== CHECKING FOR DATA ISSUES ===")
    
    # Check for orders with None order_date
    null_date_sales = db.session.query(func.count(SalesOrder.id)).filter(
        SalesOrder.order_date == None
    ).scalar() or 0
    
    null_date_pos = db.session.query(func.count(POSOrder.id)).filter(
        POSOrder.order_date == None
    ).scalar() or 0
    
    print(f"Orders with NULL order_date:")
    print(f"  - Sales Orders: {null_date_sales}")
    print(f"  - POS Orders: {null_date_pos}")
    
    # Check all orders regardless of date
    print("\n=== ALL ORDERS IN DATABASE ===")
    all_sales = SalesOrder.query.all()
    all_pos = POSOrder.query.all()
    
    print(f"All Sales Orders: {len(all_sales)}")
    for order in all_sales:
        print(f"  - Order {order.name}, Date: {order.order_date}, State: {order.state}")
    
    print(f"\nAll POS Orders: {len(all_pos)}")
    for order in all_pos:
        print(f"  - Order {order.name}, Date: {order.order_date}, State: {order.state}")
    
    # Check if the current month filter is working correctly
    print("\n=== CHECKING MONTH FILTERING ===")
    print(f"Current month: {first_day_of_month.month}/{first_day_of_month.year}")
    
    # Check orders by month
    for month in range(1, 13):
        month_start = datetime(now.year, month, 1)
        if month < 12:
            month_end = datetime(now.year, month + 1, 1)
        else:
            month_end = datetime(now.year + 1, 1, 1)
        
        sales_count = db.session.query(func.count(SalesOrder.id)).filter(
            SalesOrder.order_date >= month_start,
            SalesOrder.order_date < month_end
        ).scalar() or 0
        
        pos_count = db.session.query(func.count(POSOrder.id)).filter(
            POSOrder.order_date >= month_start,
            POSOrder.order_date < month_end
        ).scalar() or 0
        
        total = sales_count + pos_count
        
        print(f"Month {month}/{now.year}: {total} orders ({sales_count} sales, {pos_count} POS)")
