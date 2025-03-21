from flask import Flask
from extensions import db
from modules.sales.models import SalesOrder
from modules.pos.models import POSOrder
from datetime import datetime
from config import config

# Create the app
app = Flask(__name__)
app.config.from_object(config['default'])
config['default'].init_app(app)
db.init_app(app)

with app.app_context():
    first_day_of_month = datetime(datetime.utcnow().year, datetime.utcnow().month, 1)
    
    # Check sales orders
    sales_orders = SalesOrder.query.filter(
        SalesOrder.order_date >= first_day_of_month,
        SalesOrder.state.in_(['confirmed', 'done'])
    ).all()
    
    print(f"Sales Orders this month: {len(sales_orders)}")
    for order in sales_orders:
        print(f"  - Order {order.name}, Date: {order.order_date}, State: {order.state}")
    
    # Check POS orders
    pos_orders = POSOrder.query.filter(
        POSOrder.order_date >= first_day_of_month,
        POSOrder.state == 'paid'
    ).all()
    
    print(f"\nPOS Orders this month: {len(pos_orders)}")
    for order in pos_orders:
        print(f"  - Order {order.name}, Date: {order.order_date}, State: {order.state}")
    
    print(f"\nTotal Orders: {len(sales_orders) + len(pos_orders)}")
    
    # Check all orders regardless of date/state
    all_sales = SalesOrder.query.all()
    all_pos = POSOrder.query.all()
    
    print(f"\nAll Sales Orders in database: {len(all_sales)}")
    print(f"All POS Orders in database: {len(all_pos)}")
    
    # Check orders with different states
    draft_sales = SalesOrder.query.filter(SalesOrder.state == 'draft').count()
    confirmed_sales = SalesOrder.query.filter(SalesOrder.state == 'confirmed').count()
    done_sales = SalesOrder.query.filter(SalesOrder.state == 'done').count()
    cancelled_sales = SalesOrder.query.filter(SalesOrder.state == 'cancelled').count()
    
    print(f"\nSales Orders by state:")
    print(f"  - Draft: {draft_sales}")
    print(f"  - Confirmed: {confirmed_sales}")
    print(f"  - Done: {done_sales}")
    print(f"  - Cancelled: {cancelled_sales}")
    
    # Check POS orders with different states
    draft_pos = POSOrder.query.filter(POSOrder.state == 'draft').count()
    paid_pos = POSOrder.query.filter(POSOrder.state == 'paid').count()
    cancelled_pos = POSOrder.query.filter(POSOrder.state == 'cancelled').count()
    
    print(f"\nPOS Orders by state:")
    print(f"  - Draft: {draft_pos}")
    print(f"  - Paid: {paid_pos}")
    print(f"  - Cancelled: {cancelled_pos}")
