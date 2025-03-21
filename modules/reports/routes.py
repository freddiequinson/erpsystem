from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required
from datetime import datetime, timedelta, date
import calendar
import json
from sqlalchemy import func, desc, or_

from . import reports_bp
from modules.inventory.models import Product, StockMove, StockLocation
from modules.sales.models import SalesOrder, SalesOrderLine, Customer, Invoice, Payment
from modules.pos.models import POSOrder, POSOrderLine, POSSession, POSReturn, POSReturnLine
from modules.employees.models import Employee
from modules.auth.models import User
from app import db

@reports_bp.route('/')
@login_required
def index():
    """Main reporting dashboard"""
    # Get quick stats for dashboard
    today = datetime.now().date()
    month_start = datetime(today.year, today.month, 1)
    
    # Sales stats
    today_sales = db.session.query(func.sum(POSOrder.total_amount)).filter(
        func.date(POSOrder.order_date) == today,
        POSOrder.state == 'paid'
    ).scalar() or 0
    
    # Get today's returns
    today_returns = db.session.query(func.sum(POSReturn.refund_amount)).filter(
        func.date(POSReturn.return_date) == today,
        POSReturn.state == 'validated'
    ).scalar() or 0
    
    # Calculate net sales (sales minus returns)
    today_net_sales = max(0, today_sales - today_returns)
    
    monthly_sales = db.session.query(func.sum(POSOrder.total_amount)).filter(
        POSOrder.order_date >= month_start,
        POSOrder.state == 'paid'
    ).scalar() or 0
    
    # Get monthly returns
    monthly_returns = db.session.query(func.sum(POSReturn.refund_amount)).filter(
        POSReturn.return_date >= month_start,
        POSReturn.state == 'validated'
    ).scalar() or 0
    
    # Calculate net monthly sales
    monthly_net_sales = max(0, monthly_sales - monthly_returns)
    
    total_orders = POSOrder.query.filter(POSOrder.state == 'paid').count()
    
    # Low stock count
    low_stock_count = 0
    products = Product.query.filter(Product.is_active == True).all()
    for product in products:
        if hasattr(product, 'available_quantity') and product.available_quantity < 5:
            low_stock_count += 1
    
    context = {
        'today_sales': today_net_sales,
        'today_returns': today_returns,
        'monthly_sales': monthly_net_sales,
        'monthly_returns': monthly_returns,
        'total_orders': total_orders,
        'low_stock_count': low_stock_count
    }
    
    return render_template('reports/index.html', title="Reports Dashboard", **context)

@reports_bp.route('/sales')
@login_required
def sales_report():
    """Sales report page"""
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        end_date = end_date.replace(hour=23, minute=59, second=59)
    else:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
    
    # Get real sales data
    sales_data = get_real_sales_data(start_date, end_date)
    
    # Debug the data being sent to the template
    print(f"Final sales data structure: {sales_data}")
    
    # Convert data to JSON and back to ensure it's serializable
    import json
    try:
        sales_data_json = json.dumps(sales_data)
        print(f"Serialized sales data: {sales_data_json[:100]}...")  # Print first 100 chars
        sales_data = json.loads(sales_data_json)
    except Exception as e:
        print(f"Error serializing sales data: {e}")
        # Provide default values if serialization fails
        sales_data = {
            'daily_sales': {'labels': [], 'values': []},
            'top_products': {'products': [], 'labels': [], 'values': [], 'quantities': []},
            'payment_methods': {'labels': [], 'values': []},
            'total_sales': 0,
            'total_orders': 0,
            'avg_order_value': 0
        }
    
    return render_template(
        'reports/sales_report.html',
        title="Sales Report",
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        sales_data=sales_data
    )

@reports_bp.route('/inventory')
@login_required
def inventory_report():
    """Inventory report page"""
    # Get all products with their inventory levels
    products = Product.query.filter_by(is_active=True).all()
    
    # Get all stock locations (internal only)
    stock_locations = StockLocation.query.filter_by(location_type='internal').all()
    
    # Get recent stock movements
    recent_stock_moves = StockMove.query.order_by(StockMove.created_at.desc()).limit(10).all()
    
    # Calculate inventory statistics
    total_products = len(products)
    low_stock_products = [p for p in products if p.available_quantity < p.min_stock]
    low_stock_count = len(low_stock_products)
    out_of_stock_count = len([p for p in products if p.available_quantity <= 0])
    
    # Calculate total inventory value - ensure we only count positive quantities
    total_inventory_value = sum(p.available_quantity * p.cost_price for p in products if p.available_quantity > 0)
    
    # Get top products by value (quantity * cost)
    top_value_products = sorted(
        [p for p in products if p.available_quantity > 0], 
        key=lambda p: p.available_quantity * p.cost_price, 
        reverse=True
    )[:5]
    
    # Get top moving products (based on recent stock movements)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    top_moving_product_ids = db.session.query(
        StockMove.product_id, 
        func.sum(StockMove.quantity).label('total_moved')
    ).filter(
        StockMove.state == 'done',
        StockMove.created_at >= thirty_days_ago
    ).group_by(
        StockMove.product_id
    ).order_by(
        desc('total_moved')
    ).limit(5).all()
    
    # Get the actual product objects and their moved quantities
    top_moving_products = []
    for product_id, quantity_moved in top_moving_product_ids:
        product = Product.query.get(product_id)
        if product:
            product.quantity_moved = quantity_moved
            top_moving_products.append(product)
    
    context = {
        'products': products,
        'stock_locations': stock_locations,
        'recent_stock_moves': recent_stock_moves,
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'total_inventory_value': total_inventory_value,
        'top_value_products': top_value_products,
        'top_moving_products': top_moving_products,
        'low_stock_products': low_stock_products[:10]  # Show only top 10 low stock products
    }
    
    return render_template('reports/inventory_report.html', title="Inventory Report", **context)

@reports_bp.route('/employee-report')
@login_required
def employee_report():
    """Redirect to the manager's sales worker dashboard"""
    flash('Employee performance reports have been consolidated into the Sales Worker Monitoring dashboard.', 'info')
    return redirect(url_for('manager.sales_worker_dashboard', **request.args))

@reports_bp.route('/export-employee-report')
@login_required
def export_employee_report():
    """Redirect to the manager's export employee report functionality"""
    return redirect(url_for('manager.export_employee_report', **request.args))

@reports_bp.route('/api/sales-data')
@login_required
def api_sales_data():
    """API endpoint for sales data"""
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        end_date = end_date.replace(hour=23, minute=59, second=59)
    else:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
    
    sales_data = get_real_sales_data(start_date, end_date)
    
    return jsonify(sales_data)

@reports_bp.route('/api/low-stock-count')
@login_required
def api_low_stock_count():
    """API endpoint for low stock count"""
    low_stock_count = 0
    products = Product.query.filter(Product.is_active == True).all()
    for product in products:
        if hasattr(product, 'available_quantity') and product.available_quantity < 5:
            low_stock_count += 1
    
    return jsonify({'count': low_stock_count})

def get_real_sales_data(start_date, end_date):
    """Get real sales data from the database"""
    print(f"Getting real sales data between {start_date} and {end_date}")
    
    # Initialize default values
    total_sales = 0
    total_orders = 0
    avg_order_value = 0
    
    # Get daily sales
    try:
        # Debug query parameters
        print(f"Daily sales query parameters: start_date={start_date}, end_date={end_date}")
        
        # First check if we have any orders in the system
        order_count = db.session.query(POSOrder).filter(POSOrder.state == 'paid').count()
        print(f"Total paid orders in system: {order_count}")
        
        # Query to get daily sales data (adjusted for returns)
        daily_sales_query = db.session.query(
            func.date(POSOrder.order_date).label('date'),
            func.sum(POSOrder.total_amount).label('total')
        ).filter(
            POSOrder.state == 'paid'
        ).group_by(func.date(POSOrder.order_date)).all()
        
        # Query to get daily returns data
        daily_returns_query = db.session.query(
            func.date(POSReturn.return_date).label('date'),
            func.sum(POSReturn.refund_amount).label('total')
        ).filter(
            POSReturn.state == 'validated'
        ).group_by(func.date(POSReturn.return_date)).all()
        
        # Convert returns data to a dictionary for easy lookup
        returns_by_date = {r[0].strftime('%Y-%m-%d'): float(r[1]) for r in daily_returns_query}
        
        print(f"Daily sales query result count: {len(daily_sales_query)}")
        print(f"Daily returns query result count: {len(daily_returns_query)}")
        
        dates = []
        sales_values = []
        returns_values = []
        net_sales_values = []
        
        # Create a date range from start_date to end_date
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            dates.append(date_str)
            
            # Find if we have sales for this date
            sales_for_date = next((float(s[1]) for s in daily_sales_query if s[0].strftime('%Y-%m-%d') == date_str), 0)
            
            # Find if we have returns for this date
            returns_for_date = returns_by_date.get(date_str, 0)
            
            # Calculate net sales (sales minus returns)
            net_sales_for_date = sales_for_date - returns_for_date
            
            sales_values.append(sales_for_date)
            returns_values.append(returns_for_date)
            net_sales_values.append(net_sales_for_date)
            
            print(f"Date: {date_str}, Sales: {sales_for_date}, Returns: {returns_for_date}, Net: {net_sales_for_date}")
            
            current_date += timedelta(days=1)
            
        # If we don't have any sales data, create sample data for demonstration
        if not any(sales_values) and order_count == 0:
            print("No sales data found. Creating sample data for demonstration.")
            # Generate random sales data between 100 and 1000 for demonstration
            import random
            sales_values = [round(random.uniform(100, 1000), 2) for _ in range(len(dates))]
            returns_values = [0] * len(dates)
            net_sales_values = sales_values.copy()
            print(f"Sample sales values: {sales_values}")
            
    except Exception as e:
        print(f"Error getting daily sales: {e}")
        import traceback
        traceback.print_exc()
        dates = []
        sales_values = []
        returns_values = []
        net_sales_values = []
    
    # Get top selling products (adjusted for returns)
    try:
        # Query to get top selling products
        top_products_query = db.session.query(
            Product.name,
            func.sum(POSOrderLine.quantity).label('qty_sold'),
            func.sum(POSOrderLine.quantity * POSOrderLine.unit_price).label('total_sales')
        ).join(
            POSOrderLine, POSOrderLine.product_id == Product.id
        ).join(
            POSOrder, POSOrder.id == POSOrderLine.order_id
        ).filter(
            POSOrder.order_date.between(start_date, end_date),
            POSOrder.state == 'paid'
        ).group_by(Product.id).order_by(
            func.sum(POSOrderLine.quantity * POSOrderLine.unit_price).desc()
        ).limit(5).all()
        
        # Query to get returned products
        returned_products_query = db.session.query(
            Product.id,
            Product.name,
            func.sum(POSReturnLine.quantity).label('qty_returned'),
            func.sum(POSReturnLine.quantity * POSReturnLine.unit_price).label('total_returns')
        ).join(
            POSReturnLine, POSReturnLine.product_id == Product.id
        ).join(
            POSReturn, POSReturn.id == POSReturnLine.return_id
        ).filter(
            POSReturn.return_date.between(start_date, end_date),
            POSReturn.state == 'validated'
        ).group_by(Product.id).all()
        
        # Convert returned products to a dictionary for easy lookup
        returned_products = {r[0]: {'name': r[1], 'qty': float(r[2]), 'value': float(r[3])} for r in returned_products_query}
        
        print(f"Top products query result count: {len(top_products_query)}")
        print(f"Returned products query result count: {len(returned_products_query)}")
        
        products = []
        quantities = []
        product_sales = []
        
        for p in top_products_query:
            product_name = p[0]
            quantity_sold = float(p[1]) if p[1] is not None else 0
            sales_value = float(p[2]) if p[2] is not None else 0
            
            # Find the product ID to check for returns
            product = Product.query.filter_by(name=product_name).first()
            if product and product.id in returned_products:
                # Adjust for returns
                returned_qty = returned_products[product.id]['qty']
                returned_value = returned_products[product.id]['value']
                
                # Calculate net values
                quantity_sold = max(0, quantity_sold - returned_qty)
                sales_value = max(0, sales_value - returned_value)
            
            products.append(product_name)
            quantities.append(quantity_sold)
            product_sales.append(sales_value)
            
            print(f"Product: {product_name}, Quantity: {quantity_sold}, Sales: {sales_value}")
            
    except Exception as e:
        print(f"Error getting top products: {e}")
        import traceback
        traceback.print_exc()
        products = []
        quantities = []
        product_sales = []
    
    # Get payment methods distribution
    try:
        payment_methods_query = db.session.query(
            POSOrder.payment_method,
            func.sum(POSOrder.total_amount).label('total')
        ).filter(
            POSOrder.order_date.between(start_date, end_date),
            POSOrder.state == 'paid'
        ).group_by(POSOrder.payment_method).all()
        
        # Get returns by payment method (refund method)
        returns_by_method_query = db.session.query(
            POSReturn.refund_method,
            func.sum(POSReturn.refund_amount).label('total')
        ).filter(
            POSReturn.return_date.between(start_date, end_date),
            POSReturn.state == 'validated'
        ).group_by(POSReturn.refund_method).all()
        
        # Convert returns by method to a dictionary for easy lookup
        returns_by_method = {r[0]: float(r[1]) for r in returns_by_method_query}
        
        print(f"Payment methods query result count: {len(payment_methods_query)}")
        print(f"Returns by method query result count: {len(returns_by_method_query)}")
        
        payment_methods = []
        payment_values = []
        
        for method, value in payment_methods_query:
            # Adjust for returns if the same method was used for refunds
            refund_value = returns_by_method.get(method, 0)
            net_value = max(0, float(value) - refund_value)
            
            payment_methods.append(method)
            payment_values.append(net_value)
        
    except Exception as e:
        print(f"Error getting payment methods: {e}")
        payment_methods = []
        payment_values = []
    
    # Calculate totals (adjusted for returns)
    try:
        # Get total sales
        total_sales_query = db.session.query(
            func.sum(POSOrder.total_amount)
        ).filter(
            POSOrder.order_date.between(start_date, end_date),
            POSOrder.state == 'paid'
        ).scalar()
        
        # Get total returns
        total_returns_query = db.session.query(
            func.sum(POSReturn.refund_amount)
        ).filter(
            POSReturn.return_date.between(start_date, end_date),
            POSReturn.state == 'validated'
        ).scalar()
        
        # Calculate net sales (sales minus returns)
        total_sales_raw = float(total_sales_query) if total_sales_query is not None else 0
        total_returns = float(total_returns_query) if total_returns_query is not None else 0
        total_sales = max(0, total_sales_raw - total_returns)
        
        print(f"Total sales: {total_sales_raw}")
        print(f"Total returns: {total_returns}")
        print(f"Net sales: {total_sales}")
        
        # Get total orders
        total_orders_query = db.session.query(
            func.count(POSOrder.id)
        ).filter(
            POSOrder.order_date.between(start_date, end_date),
            POSOrder.state == 'paid'
        ).scalar()
        
        total_orders = int(total_orders_query) if total_orders_query is not None else 0
        print(f"Total orders: {total_orders}")
        
        # Calculate average order value
        avg_order_value = round(total_sales / total_orders, 2) if total_orders > 0 else 0
        print(f"Average order value: {avg_order_value}")
        
    except Exception as e:
        print(f"Error calculating totals: {e}")
        import traceback
        traceback.print_exc()
        total_sales = 0
        total_orders = 0
        avg_order_value = 0
    
    # Prepare data for charts
    sales_data = {
        'daily_sales': {
            'labels': dates,
            'values': sales_values,
            'returns': returns_values,
            'net_sales': net_sales_values
        },
        'top_products': {
            'labels': products,
            'values': product_sales,
            'quantities': quantities,
            'products': [
                {'name': products[i], 'quantity': quantities[i], 'sales': product_sales[i]} 
                for i in range(len(products)) if i < len(quantities) and i < len(product_sales)
            ]
        },
        'payment_methods': {
            'labels': payment_methods,
            'values': payment_values
        },
        'total_sales': total_sales,
        'total_orders': total_orders,
        'avg_order_value': avg_order_value,
        'total_returns': total_returns
    }
    
    # Debug the final data structure
    print("Final sales data structure:")
    print(json.dumps(sales_data, indent=2, default=str))
    
    return sales_data

def get_real_inventory_data():
    """Get real inventory data from the database"""
    # Get low stock products
    low_stock_products = []
    products = Product.query.filter(Product.is_active == True).all()
    
    for product in products:
        if hasattr(product, 'available_quantity') and product.available_quantity < product.min_stock:
            low_stock_products.append({
                "id": product.id,
                "name": product.name,
                "qty_available": product.available_quantity,
                "min_qty": product.min_stock
            })
    
    # Sort by available quantity (ascending)
    low_stock_products.sort(key=lambda p: p["qty_available"])
    
    # Get top moving products (based on sales in the last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    try:
        top_moving_query = db.session.query(
            Product.name,
            func.sum(POSOrderLine.quantity).label('qty_sold')
        ).join(
            POSOrderLine, POSOrderLine.product_id == Product.id
        ).join(
            POSOrder, POSOrder.id == POSOrderLine.order_id
        ).filter(
            POSOrder.order_date.between(start_date, end_date),
            POSOrder.state == 'paid'
        ).group_by(Product.id).order_by(func.sum(POSOrderLine.quantity).desc()).limit(10).all()
        
        top_moving_products = [p[0] for p in top_moving_query]
        quantities = [int(p[1]) for p in top_moving_query]
    except Exception as e:
        print(f"Error getting top moving products: {e}")
        top_moving_products = []
        quantities = []
    
    # Calculate total inventory value
    try:
        inventory_value = 0
        for product in products:
            if hasattr(product, 'available_quantity') and hasattr(product, 'cost_price'):
                inventory_value += product.available_quantity * product.cost_price
    except Exception as e:
        print(f"Error calculating inventory value: {e}")
        inventory_value = 0
    
    # Get top products by value (quantity * cost)
    top_value_products = sorted(
        products, 
        key=lambda p: p.available_quantity * p.cost_price if p.available_quantity > 0 else 0, 
        reverse=True
    )[:5]
    
    return {
        'low_stock_products': low_stock_products,
        'top_moving_products': top_moving_products,
        'quantities': quantities,
        'inventory_value': inventory_value,
        'top_value_products': top_value_products
    }

def get_real_employee_data(start_date, end_date):
    """Get real employee performance data from the database"""
    # Get date range (default to last 30 days)
    print(f"Fetching employee data from {start_date} to {end_date}")
    
    try:
        # First, let's get all employees
        all_employees = Employee.query.all()
        print(f"Found {len(all_employees)} total employees")
        
        # Create a dictionary to store employee data
        employees = []
        for emp in all_employees:
            # Get sales data for this employee
            sales_data = db.session.query(
                func.sum(POSOrder.total_amount).label('total_sales'),
                func.count(POSOrder.id).label('total_orders'),
                func.sum(POSOrderLine.qty).label('total_items')
            ).filter(
                POSOrder.employee_id == emp.id,
                POSOrder.order_date.between(start_date, end_date),
                POSOrder.state == 'paid'
            ).first()
            
            # Get returns data for this employee
            returns_data = db.session.query(
                func.sum(POSReturn.refund_amount).label('total_returns')
            ).filter(
                POSReturn.employee_id == emp.id,
                POSReturn.return_date.between(start_date, end_date),
                POSReturn.state == 'validated'
            ).first()
            
            # Get attendance data (hours worked) - using User ID
            attendance_data = None
            if emp.user_id:
                attendance_data = db.session.query(
                    func.count(POSSession.id).label('session_count'),
                    func.sum(func.julianday(POSSession.end_time) - func.julianday(POSSession.start_time)).label('hours_worked')
                ).filter(
                    POSSession.user_id == emp.user_id,
                    POSSession.start_time.between(start_date, end_date),
                    POSSession.state == 'closed'
                ).first()
            
            # Extract values with proper null handling
            total_sales_value = float(sales_data[0]) if sales_data and sales_data[0] is not None else 0
            total_orders_value = int(sales_data[1]) if sales_data and sales_data[1] is not None else 0
            total_items_value = int(sales_data[2]) if sales_data and sales_data[2] is not None else 0
            total_returns_value = float(returns_data[0]) if returns_data and returns_data[0] is not None else 0
            
            # Calculate net sales (sales minus returns)
            net_sales_value = max(0, total_sales_value - total_returns_value)
            
            hours_worked = float(attendance_data[1]) * 24 if attendance_data and attendance_data[1] is not None else 0
            session_count = int(attendance_data[0]) if attendance_data and attendance_data[0] is not None else 0
            
            # Calculate derived metrics
            sales_per_hour = (net_sales_value / hours_worked) if hours_worked > 0 else 0
            orders_per_hour = (total_orders_value / hours_worked) if hours_worked > 0 else 0
            avg_order_value = (net_sales_value / total_orders_value) if total_orders_value > 0 else 0
            avg_session_duration = (hours_worked / session_count) if session_count > 0 else 0
            
            employees.append({
                "id": emp.id,
                "first_name": emp.first_name,
                "last_name": emp.last_name,
                "full_name": f"{emp.first_name} {emp.last_name}",
                "total_sales": net_sales_value,
                "gross_sales": total_sales_value,
                "total_returns": total_returns_value,
                "total_orders": total_orders_value,
                "total_items": total_items_value,
                "sales_percentage": 0,  # Will calculate after all employees are processed
                "avg_order_value": avg_order_value,
                "hours_worked": hours_worked,
                "session_count": session_count,
                "avg_session_duration": avg_session_duration,
                "sales_per_hour": sales_per_hour,
                "orders_per_hour": orders_per_hour,
                "sales_efficiency": min(sales_per_hour / 50 * 100, 100) if sales_per_hour > 0 else 0  # Normalize to 100%
            })
        
        # Calculate total sales for percentage calculations
        total_sales = sum(emp["total_sales"] for emp in employees)
        
        # Update sales percentages
        for emp in employees:
            emp["sales_percentage"] = (emp["total_sales"] / total_sales * 100) if total_sales > 0 else 0
        
        # Sort employees by total sales (descending)
        employees.sort(key=lambda x: x["total_sales"], reverse=True)
        
    except Exception as e:
        print(f"Error getting employee data: {e}")
        employees = []
    
    # Format data for charts
    employee_sales_data = {
        'labels': [emp["full_name"] for emp in employees],
        'values': [emp["total_sales"] for emp in employees],
        'orders': [emp["total_orders"] for emp in employees],
        'items': [emp["total_items"] for emp in employees],
        'hours': [emp["hours_worked"] for emp in employees],
        'sales_per_hour': [emp["sales_per_hour"] for emp in employees],
        'orders_per_hour': [emp["orders_per_hour"] for emp in employees]
    }
    
    chart_data = {
        'employee_names': [emp["full_name"] for emp in employees],
        'employee_sales': [emp["total_sales"] for emp in employees],
        'employee_returns': [emp["total_returns"] for emp in employees],
        'employee_gross_sales': [emp["gross_sales"] for emp in employees],
        'employee_orders': [emp["total_orders"] for emp in employees],
        'employee_hours': [emp["hours_worked"] for emp in employees],
        'sales_per_hour': [emp["sales_per_hour"] for emp in employees],
    }
    
    return {
        'top_employees': employees,
        'employee_sales': employee_sales_data,
        'chart_data': chart_data
    }
