from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from extensions import db
from modules.sales.models import Customer, SalesOrder, SalesOrderLine, Invoice, InvoiceLine, Payment
from modules.sales.forms import CustomerForm, SalesOrderForm, InvoiceForm, PaymentForm
from modules.inventory.models import Product, StockMove, StockLocation
from modules.pos.models import POSOrder, POSOrderLine
from datetime import datetime, timedelta
import json
import io
import csv
from sqlalchemy import func, desc, extract, text
from modules.auth.models import User

sales = Blueprint('sales', __name__, url_prefix='/sales')

# Dashboard
@sales.route('/')
@login_required
def dashboard():
    """Sales dashboard"""
    from modules.inventory.models import Product
    from datetime import datetime, timedelta
    import sys
    
    now = datetime.utcnow()
    first_day_of_month = datetime(now.year, now.month, 1)
    last_day_of_month = datetime(now.year, now.month, 1) + timedelta(days=31)
    last_day_of_month = last_day_of_month.replace(day=1) - timedelta(days=1)
    first_day_of_prev_month = (first_day_of_month - timedelta(days=1)).replace(day=1)
    
    print("===== DEBUG: SALES DASHBOARD =====", file=sys.stderr)
    print(f"Current date: {now}", file=sys.stderr)
    print(f"First day of month: {first_day_of_month}", file=sys.stderr)
    
    # Get total sales for current month (both sales orders and POS)
    # Check if user is admin or branch manager
    is_admin = current_user.has_role('admin')
    
    # Create base query for total sales orders
    total_sales_orders_query = db.session.query(func.sum(SalesOrder.total_amount)).filter(
        SalesOrder.order_date >= first_day_of_month,
        SalesOrder.order_date <= last_day_of_month,
        SalesOrder.state.in_(['confirmed', 'done'])
    )
    
    # Apply user filter for non-admin users
    if not is_admin:
        total_sales_orders_query = total_sales_orders_query.filter(
            SalesOrder.created_by == current_user.id
        )
    
    total_sales_orders = total_sales_orders_query.scalar() or 0
    
    from modules.pos.models import POSOrder
    # Create base query for total POS orders
    total_pos_orders_query = db.session.query(func.sum(POSOrder.total_amount)).filter(
        POSOrder.order_date >= first_day_of_month,
        POSOrder.order_date <= last_day_of_month,
        POSOrder.state == 'paid'
    )
    
    # Apply user filter for non-admin users
    if not is_admin:
        total_pos_orders_query = total_pos_orders_query.filter(POSOrder.created_by == current_user.id)
    
    total_pos_orders = total_pos_orders_query.scalar() or 0
    
    total_sales = total_sales_orders + total_pos_orders
    
    # Get total sales for previous month (both sales orders and POS)
    prev_month_sales_orders_query = db.session.query(func.sum(SalesOrder.total_amount)).filter(
        SalesOrder.order_date >= first_day_of_prev_month,
        SalesOrder.order_date < first_day_of_month,
        SalesOrder.state.in_(['confirmed', 'done'])
    )
    
    # Apply user filter for non-admin users
    if not is_admin:
        prev_month_sales_orders_query = prev_month_sales_orders_query.filter(SalesOrder.created_by == current_user.id)
    
    prev_month_sales_orders = prev_month_sales_orders_query.scalar() or 0
    
    prev_month_pos_orders_query = db.session.query(func.sum(POSOrder.total_amount)).filter(
        POSOrder.order_date >= first_day_of_prev_month,
        POSOrder.order_date < first_day_of_month,
        POSOrder.state == 'paid'
    )
    
    # Apply user filter for non-admin users
    if not is_admin:
        prev_month_pos_orders_query = prev_month_pos_orders_query.filter(POSOrder.created_by == current_user.id)
    
    prev_month_pos_orders = prev_month_pos_orders_query.scalar() or 0
    
    prev_month_sales = prev_month_sales_orders + prev_month_pos_orders
    
    # Count all orders regardless of state
    # For SQLite, use simpler date extraction approach
    current_year = now.year
    current_month = now.month
    
    # Get orders count for current month (both sales orders and POS)
    orders_count_sales_query = db.session.query(SalesOrder).filter(
        extract('year', SalesOrder.order_date) == current_year,
        extract('month', SalesOrder.order_date) == current_month
    )
    
    # Apply user filter for non-admin users
    if not is_admin:
        orders_count_sales_query = orders_count_sales_query.filter(SalesOrder.created_by == current_user.id)
    
    orders_count_sales = orders_count_sales_query.count()
    
    print(f"Sales orders count this month: {orders_count_sales}", file=sys.stderr)
    
    # Print all sales orders for debugging
    if is_admin:
        all_sales_orders = SalesOrder.query.all()
    else:
        all_sales_orders = SalesOrder.query.filter(SalesOrder.created_by == current_user.id).all()
    
    print(f"Total sales orders in database: {len(all_sales_orders)}", file=sys.stderr)
    for order in all_sales_orders:
        print(f"Sales Order: {order.name}, Date: {order.order_date}, State: {order.state}", file=sys.stderr)
    
    orders_count_pos_query = db.session.query(POSOrder).filter(
        extract('year', POSOrder.order_date) == current_year,
        extract('month', POSOrder.order_date) == current_month
    )
    
    # Apply user filter for non-admin users
    if not is_admin:
        orders_count_pos_query = orders_count_pos_query.filter(POSOrder.created_by == current_user.id)
    
    orders_count_pos = orders_count_pos_query.count()
    
    print(f"POS orders count this month: {orders_count_pos}", file=sys.stderr)
    
    # Print all POS orders for debugging
    if is_admin:
        all_pos_orders = POSOrder.query.all()
    else:
        all_pos_orders = POSOrder.query.filter(POSOrder.created_by == current_user.id).all()
    
    print(f"Total POS orders in database: {len(all_pos_orders)}", file=sys.stderr)
    for order in all_pos_orders:
        print(f"POS Order: {order.name}, Date: {order.order_date}, State: {order.state}", file=sys.stderr)
    
    orders_count = orders_count_sales + orders_count_pos
    print(f"Total orders count: {orders_count}", file=sys.stderr)
    
    # Get orders count for previous month (both sales orders and POS)
    prev_month = first_day_of_prev_month.month
    prev_year = first_day_of_prev_month.year
    
    prev_month_orders_sales_query = db.session.query(SalesOrder).filter(
        extract('year', SalesOrder.order_date) == prev_year,
        extract('month', SalesOrder.order_date) == prev_month
    )
    
    # Apply user filter for non-admin users
    if not is_admin:
        prev_month_orders_sales_query = prev_month_orders_sales_query.filter(SalesOrder.created_by == current_user.id)
    
    prev_month_orders_sales = prev_month_orders_sales_query.count()
    
    prev_month_orders_pos_query = db.session.query(POSOrder).filter(
        extract('year', POSOrder.order_date) == prev_year,
        extract('month', POSOrder.order_date) == prev_month
    )
    
    # Apply user filter for non-admin users
    if not is_admin:
        prev_month_orders_pos_query = prev_month_orders_pos_query.filter(POSOrder.created_by == current_user.id)
    
    prev_month_orders_pos = prev_month_orders_pos_query.count()
    
    prev_month_orders = prev_month_orders_sales + prev_month_orders_pos
    
    # Get unpaid invoices
    unpaid_invoices_query = Invoice.query.filter(Invoice.state == 'open')
    
    # Apply user filter for non-admin users
    if not is_admin:
        unpaid_invoices_query = unpaid_invoices_query.join(SalesOrder).filter(SalesOrder.created_by == current_user.id)
    
    unpaid_invoices = unpaid_invoices_query.all()
    unpaid_count = len(unpaid_invoices)
    unpaid_amount = sum(invoice.total_amount for invoice in unpaid_invoices)
    
    # Get recent orders (combining sales orders and POS orders)
    recent_sales_orders_query = SalesOrder.query
    
    # Apply user filter for non-admin users
    if not is_admin:
        recent_sales_orders_query = recent_sales_orders_query.filter(SalesOrder.created_by == current_user.id)
    
    # Apply ordering and limit after all filters
    recent_sales_orders = recent_sales_orders_query.order_by(SalesOrder.order_date.desc()).limit(5).all()
    
    recent_pos_orders_query = POSOrder.query
    
    # Apply user filter for non-admin users
    if not is_admin:
        recent_pos_orders_query = recent_pos_orders_query.filter(POSOrder.created_by == current_user.id)
    
    # Apply ordering and limit after all filters
    recent_pos_orders = recent_pos_orders_query.order_by(POSOrder.order_date.desc()).limit(5).all()
    
    # Combine and sort both types of orders by date
    combined_orders = []
    for order in recent_sales_orders:
        combined_orders.append({
            'id': order.id,
            'name': order.name,
            'order_date': order.order_date,
            'customer': order.customer,
            'state': order.state,
            'total_amount': order.total_amount,
            'type': 'sales'
        })
    
    for order in recent_pos_orders:
        combined_orders.append({
            'id': order.id,
            'name': order.name,
            'order_date': order.order_date,
            'customer': order.customer,
            'state': order.state,
            'total_amount': order.total_amount,
            'type': 'pos'
        })
    
    # Sort combined orders by date (newest first) and take the top 5
    recent_orders = sorted(combined_orders, key=lambda x: x['order_date'], reverse=True)[:5]
    
    # Get top customers (combining sales orders and POS)
    # First, get top customers from sales orders
    top_customers_sales_data_query = db.session.query(
        Customer,
        func.count(SalesOrder.id).label('orders_count'),
        func.sum(SalesOrder.total_amount).label('total_amount')
    ).join(Customer.sales_orders).filter(
        SalesOrder.state.in_(['confirmed', 'done']),
        SalesOrder.order_date >= (now - timedelta(days=90))
    )
    
    # Apply user filter for non-admin users
    if not is_admin:
        top_customers_sales_data_query = top_customers_sales_data_query.filter(SalesOrder.created_by == current_user.id)
    
    top_customers_sales_data = top_customers_sales_data_query.group_by(Customer.id).order_by(desc('total_amount')).all()
    
    # Then, get top customers from POS orders
    top_customers_pos_data_query = db.session.query(
        Customer,
        func.count(POSOrder.id).label('orders_count'),
        func.sum(POSOrder.total_amount).label('total_amount')
    ).join(Customer.pos_orders).filter(
        POSOrder.state == 'paid',
        POSOrder.order_date >= (now - timedelta(days=90))
    )
    
    # Apply user filter for non-admin users
    if not is_admin:
        top_customers_pos_data_query = top_customers_pos_data_query.filter(POSOrder.created_by == current_user.id)
    
    top_customers_pos_data = top_customers_pos_data_query.group_by(Customer.id).order_by(desc('total_amount')).all()
    
    # Combine and merge the customer data
    customer_data = {}
    for customer, orders_count, total_amount in top_customers_sales_data:
        customer_data[customer.id] = {
            'id': customer.id,
            'name': customer.name,
            'orders_count': orders_count or 0,
            'total_amount': total_amount or 0
        }
    
    for customer, orders_count, total_amount in top_customers_pos_data:
        if customer.id in customer_data:
            customer_data[customer.id]['orders_count'] += orders_count or 0
            customer_data[customer.id]['total_amount'] += total_amount or 0
        else:
            customer_data[customer.id] = {
                'id': customer.id,
                'name': customer.name,
                'orders_count': orders_count or 0,
                'total_amount': total_amount or 0
            }
    
    # Convert to list and sort by total_amount
    top_customers = sorted(customer_data.values(), key=lambda x: x['total_amount'], reverse=True)[:5]
    
    # Get top selling products (combining sales orders and POS)
    # First, get top products from sales orders
    top_products_sales_data_query = db.session.query(
        Product,
        func.sum(SalesOrderLine.quantity).label('quantity_sold'),
        func.sum(SalesOrderLine.quantity * SalesOrderLine.unit_price * (1 - SalesOrderLine.discount_percent / 100)).label('revenue')
    ).join(SalesOrderLine.product).join(SalesOrderLine.order).filter(
        SalesOrder.state.in_(['confirmed', 'done']),
        SalesOrder.order_date >= (now - timedelta(days=90))
    )
    
    # Apply user filter for non-admin users
    if not is_admin:
        top_products_sales_data_query = top_products_sales_data_query.filter(SalesOrder.created_by == current_user.id)
    
    top_products_sales_data = top_products_sales_data_query.group_by(Product.id).all()
    
    # Then, get top products from POS orders
    from modules.pos.models import POSOrderLine
    top_products_pos_data_query = db.session.query(
        Product,
        func.sum(POSOrderLine.quantity).label('quantity_sold'),
        func.sum(POSOrderLine.quantity * POSOrderLine.unit_price * (1 - POSOrderLine.discount_percent / 100)).label('revenue')
    ).join(POSOrderLine.product).join(POSOrderLine.order).filter(
        POSOrder.state == 'paid',
        POSOrder.order_date >= (now - timedelta(days=90))
    )
    
    # Apply user filter for non-admin users
    if not is_admin:
        top_products_pos_data_query = top_products_pos_data_query.filter(POSOrder.created_by == current_user.id)
    
    top_products_pos_data = top_products_pos_data_query.group_by(Product.id).all()
    
    # Combine and merge the product data
    product_data = {}
    for product, quantity_sold, revenue in top_products_sales_data:
        product_data[product.id] = {
            'id': product.id,
            'name': product.name,
            'quantity_sold': quantity_sold or 0,
            'revenue': revenue or 0
        }
    
    for product, quantity_sold, revenue in top_products_pos_data:
        if product.id in product_data:
            product_data[product.id]['quantity_sold'] += quantity_sold or 0
            product_data[product.id]['revenue'] += revenue or 0
        else:
            product_data[product.id] = {
                'id': product.id,
                'name': product.name,
                'quantity_sold': quantity_sold or 0,
                'revenue': revenue or 0
            }
    
    # Convert to list and sort by revenue
    top_products = sorted(product_data.values(), key=lambda x: x['revenue'], reverse=True)[:5]
    
    # Prepare chart data for the last 7 days (combining sales orders and POS)
    labels = []
    values = []
    
    for i in range(6, -1, -1):
        date = now - timedelta(days=i)
        labels.append(date.strftime('%a'))
        
        # Get sales for this day
        day_sales_orders_query = db.session.query(func.sum(SalesOrder.total_amount)).filter(
            func.date(SalesOrder.order_date) == date.date(),
            SalesOrder.state.in_(['confirmed', 'done'])
        )
        
        # Apply user filter for non-admin users
        if not is_admin:
            day_sales_orders_query = day_sales_orders_query.filter(SalesOrder.created_by == current_user.id)
        
        day_sales_orders = day_sales_orders_query.scalar() or 0
        
        day_pos_orders_query = db.session.query(func.sum(POSOrder.total_amount)).filter(
            func.date(POSOrder.order_date) == date.date(),
            POSOrder.state == 'paid'
        )
        
        # Apply user filter for non-admin users
        if not is_admin:
            day_pos_orders_query = day_pos_orders_query.filter(POSOrder.created_by == current_user.id)
        
        day_pos_orders = day_pos_orders_query.scalar() or 0
        
        day_sales = day_sales_orders + day_pos_orders
        
        values.append(float(day_sales))
    
    sales_data = {
        'labels': labels,
        'values': values
    }
    
    return render_template(
        'sales/dashboard.html',
        now=now,
        total_sales=total_sales,
        prev_month_sales=prev_month_sales,
        orders_count=orders_count,
        prev_month_orders=prev_month_orders,
        unpaid_amount=unpaid_amount,
        unpaid_count=unpaid_count,
        recent_orders=recent_orders,
        top_customers=top_customers,
        top_products=top_products,
        sales_data=sales_data
    )

@sales.route('/api/chart-data')
@login_required
def chart_data():
    period = request.args.get('period', 'week')
    now = datetime.now()
    labels = []
    values = []
    
    if period == 'week':
        # Last 7 days
        for i in range(6, -1, -1):
            date = now - timedelta(days=i)
            labels.append(date.strftime('%a'))
            
            # Get sales for this day
            day_sales_orders_query = db.session.query(func.sum(SalesOrder.total_amount)).filter(
                func.date(SalesOrder.order_date) == date.date(),
                SalesOrder.state.in_(['confirmed', 'done'])
            )
            
            # Apply user filter for non-admin users
            if not current_user.has_role('admin'):
                day_sales_orders_query = day_sales_orders_query.filter(SalesOrder.created_by == current_user.id)
            
            day_sales_orders = day_sales_orders_query.scalar() or 0
            
            from modules.pos.models import POSOrder
            day_pos_orders_query = db.session.query(func.sum(POSOrder.total_amount)).filter(
                func.date(POSOrder.order_date) == date.date(),
                POSOrder.state == 'paid'
            )
            
            # Apply user filter for non-admin users
            if not current_user.has_role('admin'):
                day_pos_orders_query = day_pos_orders_query.filter(POSOrder.created_by == current_user.id)
            
            day_pos_orders = day_pos_orders_query.scalar() or 0
            
            day_sales = day_sales_orders + day_pos_orders
            
            values.append(float(day_sales))
    
    elif period == 'month':
        # Last 30 days
        for i in range(29, -1, -1):
            date = now - timedelta(days=i)
            if i % 3 == 0:  # Show every 3rd day to avoid crowding
                labels.append(date.strftime('%d %b'))
            else:
                labels.append('')
            
            # Get sales for this day
            day_sales_orders_query = db.session.query(func.sum(SalesOrder.total_amount)).filter(
                func.date(SalesOrder.order_date) == date.date(),
                SalesOrder.state.in_(['confirmed', 'done'])
            )
            
            # Apply user filter for non-admin users
            if not current_user.has_role('admin'):
                day_sales_orders_query = day_sales_orders_query.filter(SalesOrder.created_by == current_user.id)
            
            day_sales_orders = day_sales_orders_query.scalar() or 0
            
            day_pos_orders_query = db.session.query(func.sum(POSOrder.total_amount)).filter(
                func.date(POSOrder.order_date) == date.date(),
                POSOrder.state == 'paid'
            )
            
            # Apply user filter for non-admin users
            if not current_user.has_role('admin'):
                day_pos_orders_query = day_pos_orders_query.filter(POSOrder.created_by == current_user.id)
            
            day_pos_orders = day_pos_orders_query.scalar() or 0
            
            day_sales = day_sales_orders + day_pos_orders
            
            values.append(float(day_sales))
    
    elif period == 'quarter':
        # Last 3 months by week
        for i in range(11, -1, -1):
            start_date = now - timedelta(days=now.weekday(), weeks=i)
            end_date = start_date + timedelta(days=6)
            
            labels.append(f"{start_date.strftime('%d %b')}-{end_date.strftime('%d %b')}")
            
            # Get sales for this week
            week_sales_orders_query = db.session.query(func.sum(SalesOrder.total_amount)).filter(
                SalesOrder.order_date >= start_date,
                SalesOrder.order_date <= end_date,
                SalesOrder.state.in_(['confirmed', 'done'])
            )
            
            # Apply user filter for non-admin users
            if not current_user.has_role('admin'):
                week_sales_orders_query = week_sales_orders_query.filter(SalesOrder.created_by == current_user.id)
            
            week_sales_orders = week_sales_orders_query.scalar() or 0
            
            week_pos_orders_query = db.session.query(func.sum(POSOrder.total_amount)).filter(
                POSOrder.order_date >= start_date,
                POSOrder.order_date <= end_date,
                POSOrder.state == 'paid'
            )
            
            # Apply user filter for non-admin users
            if not current_user.has_role('admin'):
                week_pos_orders_query = week_pos_orders_query.filter(POSOrder.created_by == current_user.id)
            
            week_pos_orders = week_pos_orders_query.scalar() or 0
            
            week_sales = week_sales_orders + week_pos_orders
            
            values.append(float(week_sales))
    
    return jsonify({
        'labels': labels,
        'values': values
    })

# Customers
@sales.route('/customers')
@login_required
def customers():
    # Check if user is admin
    is_admin = current_user.has_role('admin')
    
    # Apply user filtering for non-admin users
    if is_admin:
        customers = Customer.query.all()
    else:
        # Get customers who have orders created by the current user
        customer_ids = db.session.query(SalesOrder.customer_id).filter(
            SalesOrder.created_by == current_user.id
        ).distinct()
        
        # Also include customers from POS orders created by the current user
        pos_customer_ids = db.session.query(POSOrder.customer_id).filter(
            POSOrder.created_by == current_user.id
        ).distinct()
        
        # Combine both sets of customer IDs
        all_customer_ids = customer_ids.union(pos_customer_ids)
        
        customers = Customer.query.filter(Customer.id.in_(all_customer_ids)).all()
    
    return render_template('sales/customers.html', customers=customers)

@sales.route('/customers/new', methods=['GET', 'POST'])
@login_required
def new_customer():
    form = CustomerForm()
    
    if form.validate_on_submit():
        customer = Customer(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            city=form.city.data,
            state=form.state.data,
            zip_code=form.zip_code.data,
            country=form.country.data,
            website=form.website.data,
            tax_id=form.tax_id.data,
            notes=form.notes.data,
            is_active=form.is_active.data
        )
        
        db.session.add(customer)
        db.session.commit()
        
        flash('Customer created successfully!', 'success')
        return redirect(url_for('sales.customers'))
    
    return render_template('sales/customer_form.html', form=form, title='New Customer')

@sales.route('/customers/<int:customer_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    form = CustomerForm(obj=customer)
    
    if form.validate_on_submit():
        customer.name = form.name.data
        customer.email = form.email.data
        customer.phone = form.phone.data
        customer.address = form.address.data
        customer.city = form.city.data
        customer.state = form.state.data
        customer.zip_code = form.zip_code.data
        customer.country = form.country.data
        customer.website = form.website.data
        customer.tax_id = form.tax_id.data
        customer.notes = form.notes.data
        customer.is_active = form.is_active.data
        
        db.session.commit()
        
        flash('Customer updated successfully!', 'success')
        return redirect(url_for('sales.customers'))
    
    return render_template('sales/customer_form.html', form=form, customer=customer, title='Edit Customer')

@sales.route('/customers/<int:customer_id>/delete', methods=['POST'])
@login_required
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    
    # Check if customer has sales orders
    if customer.sales_orders.count() > 0:
        flash('Cannot delete customer with sales orders.', 'danger')
        return redirect(url_for('sales.customers'))
    
    db.session.delete(customer)
    db.session.commit()
    
    flash('Customer deleted successfully!', 'success')
    return redirect(url_for('sales.customers'))

# Sales Orders
@sales.route('/orders')
@login_required
def orders():
    # Get filter parameters
    state_filter = request.args.get('state', '')
    customer_filter = request.args.get('customer_id', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    # Check if user is admin
    is_admin = current_user.has_role('admin')
    
    # Base query
    query = SalesOrder.query
    
    # Apply user filter for non-admin users
    if not is_admin:
        query = query.filter(SalesOrder.created_by == current_user.id)
    
    # Apply filters
    if state_filter:
        query = query.filter(SalesOrder.state == state_filter)
    
    if customer_filter:
        query = query.filter(SalesOrder.customer_id == customer_filter)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(SalesOrder.order_date >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
            query = query.filter(SalesOrder.order_date <= date_to_obj)
        except ValueError:
            pass
    
    # Get all orders with applied filters
    orders = query.order_by(SalesOrder.order_date.desc()).all()
    
    # Get all customers for the filter dropdown
    # For non-admin users, only show customers with orders from the current user
    if is_admin:
        customers = Customer.query.filter_by(is_active=True).all()
    else:
        # Get customers who have orders created by the current user
        customer_ids = db.session.query(SalesOrder.customer_id).filter(
            SalesOrder.created_by == current_user.id
        ).distinct()
        customers = Customer.query.filter(Customer.id.in_(customer_ids), Customer.is_active==True).all()
    
    # Calculate totals
    total_amount = sum(order.total_amount for order in orders if order.state in ['confirmed', 'done'])
    
    # Count orders by state with user filtering for non-admin users
    if is_admin:
        draft_count = SalesOrder.query.filter_by(state='draft').count()
        confirmed_count = SalesOrder.query.filter_by(state='confirmed').count()
        done_count = SalesOrder.query.filter_by(state='done').count()
        cancelled_count = SalesOrder.query.filter_by(state='cancelled').count()
    else:
        # Apply user filter to counts
        draft_count = SalesOrder.query.filter_by(state='draft').filter(SalesOrder.created_by == current_user.id).count()
        confirmed_count = SalesOrder.query.filter_by(state='confirmed').filter(SalesOrder.created_by == current_user.id).count()
        done_count = SalesOrder.query.filter_by(state='done').filter(SalesOrder.created_by == current_user.id).count()
        cancelled_count = SalesOrder.query.filter_by(state='cancelled').filter(SalesOrder.created_by == current_user.id).count()
    
    return render_template(
        'sales/orders.html',
        orders=orders,
        customers=customers,
        state_filter=state_filter,
        customer_filter=customer_filter,
        date_from=date_from,
        date_to=date_to,
        total_amount=total_amount,
        draft_count=draft_count,
        confirmed_count=confirmed_count,
        done_count=done_count,
        cancelled_count=cancelled_count
    )

@sales.route('/orders/new', methods=['GET', 'POST'])
@login_required
def new_order():
    form = SalesOrderForm()
    
    # Check if user is admin
    is_admin = current_user.has_role('admin')
    
    # Filter customers based on user's orders for non-admin users
    if is_admin:
        form.customer_id.choices = [(c.id, c.name) for c in Customer.query.filter_by(is_active=True).all()]
    else:
        # Get customers who have orders created by the current user
        customer_ids = db.session.query(SalesOrder.customer_id).filter(
            SalesOrder.created_by == current_user.id
        ).distinct()
        customers = Customer.query.filter(Customer.id.in_(customer_ids), Customer.is_active==True).all()
        
        # If no customers found, show all active customers
        if not customers:
            customers = Customer.query.filter_by(is_active=True).all()
            
        form.customer_id.choices = [(c.id, c.name) for c in customers]
    
    if form.validate_on_submit():
        # Generate order name (e.g., SO0001)
        last_order = SalesOrder.query.order_by(SalesOrder.id.desc()).first()
        order_number = 1
        if last_order:
            order_number = last_order.id + 1
        
        order_name = f"SO{order_number:04d}"
        
        order = SalesOrder(
            name=order_name,
            customer_id=form.customer_id.data,
            order_date=form.order_date.data,
            expected_date=form.expected_date.data,
            notes=form.notes.data,
            created_by=current_user.id,
            created_at=datetime.utcnow()
        )
        
        db.session.add(order)
        db.session.commit()
        
        flash('Sales order created successfully!', 'success')
        return redirect(url_for('sales.edit_order', order_id=order.id))
    
    return render_template('sales/order_form.html', form=form, title='New Sales Order')

@sales.route('/orders/<int:order_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_order(order_id):
    order = SalesOrder.query.get_or_404(order_id)
    
    # Check if user is admin
    is_admin = current_user.has_role('admin')
    
    # Check if the order belongs to the current user for non-admin users
    if not is_admin:
        # If the order was not created by the current user, deny access
        if order.created_by != current_user.id:
            flash('You do not have permission to edit this order.', 'danger')
            return redirect(url_for('sales.orders'))
    
    form = SalesOrderForm(obj=order)
    
    # Filter customers based on user's orders for non-admin users
    if is_admin:
        form.customer_id.choices = [(c.id, c.name) for c in Customer.query.filter_by(is_active=True).all()]
    else:
        # Get customers who have orders created by the current user
        customer_ids = db.session.query(SalesOrder.customer_id).filter(
            SalesOrder.created_by == current_user.id
        ).distinct()
        customers = Customer.query.filter(Customer.id.in_(customer_ids), Customer.is_active==True).all()
        
        # Add the current order's customer if not in the list
        current_customer = Customer.query.get(order.customer_id)
        if current_customer and current_customer.id not in [c.id for c in customers]:
            customers.append(current_customer)
            
        form.customer_id.choices = [(c.id, c.name) for c in customers]
    
    if form.validate_on_submit():
        order.customer_id = form.customer_id.data
        order.order_date = form.order_date.data
        order.expected_date = form.expected_date.data
        order.notes = form.notes.data
        
        db.session.commit()
        
        flash('Sales order updated successfully!', 'success')
        return redirect(url_for('sales.orders'))
    
    return render_template('sales/order_form.html', form=form, order=order, title='Edit Sales Order')

@sales.route('/orders/<int:order_id>/confirm', methods=['POST'])
@login_required
def confirm_order(order_id):
    order = SalesOrder.query.get_or_404(order_id)
    
    # Check if user is admin
    is_admin = current_user.has_role('admin')
    
    # Check if the order belongs to the current user for non-admin users
    if not is_admin:
        # If the order was not created by the current user, deny access
        if order.created_by != current_user.id:
            flash('You do not have permission to confirm this order.', 'danger')
            return redirect(url_for('sales.orders'))
    
    if order.state != 'draft':
        flash('Order is already confirmed or completed.', 'warning')
        return redirect(url_for('sales.orders'))
    
    if not order.lines.count():
        flash('Cannot confirm an order with no lines.', 'danger')
        return redirect(url_for('sales.edit_order', order_id=order.id))
    
    order.state = 'confirmed'
    db.session.commit()
    
    flash('Sales order confirmed successfully!', 'success')
    return redirect(url_for('sales.orders'))

@sales.route('/orders/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    order = SalesOrder.query.get_or_404(order_id)
    
    # Check if user is admin
    is_admin = current_user.has_role('admin')
    
    # Check if the order belongs to the current user for non-admin users
    if not is_admin:
        # If the order was not created by the current user, deny access
        if order.created_by != current_user.id:
            flash('You do not have permission to cancel this order.', 'danger')
            return redirect(url_for('sales.orders'))
    
    if order.state == 'done':
        flash('Cannot cancel a completed order.', 'danger')
        return redirect(url_for('sales.orders'))
    
    order.state = 'cancelled'
    db.session.commit()
    
    flash('Sales order cancelled successfully!', 'success')
    return redirect(url_for('sales.orders'))

@sales.route('/orders/<int:order_id>/complete', methods=['POST'])
@login_required
def complete_order(order_id):
    order = SalesOrder.query.get_or_404(order_id)
    
    # Check if user is admin
    is_admin = current_user.has_role('admin')
    
    # Check if the order belongs to the current user for non-admin users
    if not is_admin:
        # If the order was not created by the current user, deny access
        if order.created_by != current_user.id:
            flash('You do not have permission to complete this order.', 'danger')
            return redirect(url_for('sales.orders'))
    
    if order.state != 'confirmed':
        flash('Only confirmed orders can be completed.', 'danger')
        return redirect(url_for('sales.orders'))
    
    order.state = 'done'
    db.session.commit()
    
    flash('Sales order completed successfully!', 'success')
    return redirect(url_for('sales.orders'))

@sales.route('/orders/<int:order_id>/create-invoice', methods=['POST'])
@login_required
def create_invoice(order_id):
    order = SalesOrder.query.get_or_404(order_id)
    
    # Check if user is admin
    is_admin = current_user.has_role('admin')
    
    # Check if the order belongs to the current user for non-admin users
    if not is_admin:
        # If the order was not created by the current user, deny access
        if order.created_by != current_user.id:
            flash('You do not have permission to create an invoice for this order.', 'danger')
            return redirect(url_for('sales.orders'))
    
    if order.state not in ['confirmed', 'done']:
        flash('Can only create invoices for confirmed or completed orders.', 'danger')
        return redirect(url_for('sales.orders'))
    
    # Check if invoice already exists
    existing_invoice = Invoice.query.filter_by(sales_order_id=order.id).first()
    if existing_invoice:
        flash('Invoice already exists for this order.', 'warning')
        return redirect(url_for('sales.edit_invoice', invoice_id=existing_invoice.id))
    
    # Generate invoice name (e.g., INV0001)
    last_invoice = Invoice.query.order_by(Invoice.id.desc()).first()
    invoice_number = 1
    if last_invoice:
        invoice_number = last_invoice.id + 1
    
    invoice_name = f"INV{invoice_number:04d}"
    
    invoice = Invoice(
        name=invoice_name,
        customer_id=order.customer_id,
        sales_order_id=order.id,
        invoice_date=datetime.utcnow(),
        due_date=datetime.utcnow() + timedelta(days=30),
        state='draft',
        notes=f"Invoice for {order.name}",
        created_by=current_user.id,
        created_at=datetime.utcnow()
    )
    
    db.session.add(invoice)
    db.session.commit()
    
    # Create invoice lines from order lines
    for order_line in order.lines:
        invoice_line = InvoiceLine(
            invoice_id=invoice.id,
            product_id=order_line.product_id,
            description=order_line.description,
            quantity=order_line.quantity,
            unit_price=order_line.unit_price,
            discount_percent=order_line.discount_percent,
            tax_percent=order_line.tax_percent
        )
        db.session.add(invoice_line)
    
    db.session.commit()
    
    # Calculate invoice totals
    invoice.calculate_totals()
    db.session.commit()
    
    flash('Invoice created successfully!', 'success')
    return redirect(url_for('sales.edit_invoice', invoice_id=invoice.id))

# API endpoints for order lines
@sales.route('/api/order-lines/<int:order_id>', methods=['GET'])
@login_required
def api_order_lines(order_id):
    order = SalesOrder.query.get_or_404(order_id)
    lines = []
    
    for line in order.lines:
        lines.append({
            'id': line.id,
            'product_id': line.product_id,
            'product_name': line.product.name,
            'description': line.description,
            'quantity': line.quantity,
            'unit_price': line.unit_price,
            'discount_percent': line.discount_percent,
            'tax_percent': line.tax_percent,
            'subtotal': line.subtotal,
            'tax_amount': line.tax_amount
        })
    
    return jsonify(lines)

@sales.route('/api/order-lines/<int:order_id>/add', methods=['POST'])
@login_required
def api_add_order_line(order_id):
    order = SalesOrder.query.get_or_404(order_id)
    
    if order.state != 'draft':
        return jsonify({'success': False, 'message': 'Cannot modify confirmed or completed order'}), 400
    
    data = request.json
    product_id = data.get('product_id')
    
    product = Product.query.get_or_404(product_id)
    
    line = SalesOrderLine(
        order_id=order.id,
        product_id=product_id,
        description=product.name,
        quantity=data.get('quantity', 1.0),
        unit_price=data.get('unit_price', product.sale_price),
        discount_percent=data.get('discount_percent', 0.0),
        tax_percent=data.get('tax_percent', 0.0)
    )
    
    db.session.add(line)
    db.session.commit()
    
    # Update order totals
    order.calculate_totals()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'line': {
            'id': line.id,
            'product_id': line.product_id,
            'product_name': product.name,
            'description': line.description,
            'quantity': line.quantity,
            'unit_price': line.unit_price,
            'discount_percent': line.discount_percent,
            'tax_percent': line.tax_percent,
            'subtotal': line.subtotal,
            'tax_amount': line.tax_amount
        }
    })

@sales.route('/api/order-lines/<int:line_id>/update', methods=['POST'])
@login_required
def api_update_order_line(line_id):
    line = SalesOrderLine.query.get_or_404(line_id)
    
    if line.order.state != 'draft':
        return jsonify({'success': False, 'message': 'Cannot modify confirmed or completed order'}), 400
    
    data = request.json
    line.quantity = data.get('quantity', line.quantity)
    line.unit_price = data.get('unit_price', line.unit_price)
    line.discount_percent = data.get('discount_percent', line.discount_percent)
    line.tax_percent = data.get('tax_percent', line.tax_percent)
    
    db.session.commit()
    
    # Update order totals
    line.order.calculate_totals()
    db.session.commit()
    
    return jsonify({'success': True})

@sales.route('/api/order-lines/<int:line_id>/delete', methods=['POST'])
@login_required
def api_delete_order_line(line_id):
    line = SalesOrderLine.query.get_or_404(line_id)
    
    if line.order.state != 'draft':
        return jsonify({'success': False, 'message': 'Cannot modify confirmed or completed order'}), 400
    
    order = line.order
    db.session.delete(line)
    db.session.commit()
    
    # Update order totals
    order.calculate_totals()
    db.session.commit()
    
    return jsonify({'success': True})

# API endpoints for invoice lines
@sales.route('/api/invoices/<int:invoice_id>/lines', methods=['GET'])
@login_required
def api_invoice_lines(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    lines = []
    
    for line in invoice.lines:
        lines.append({
            'id': line.id,
            'product_id': line.product_id,
            'product_name': line.product.name if line.product else '',
            'description': line.description,
            'quantity': line.quantity,
            'unit_price': float(line.unit_price),
            'tax_rate': float(line.tax_rate),
            'tax_amount': float(line.tax_amount),
            'subtotal': float(line.subtotal)
        })
    
    return jsonify(lines)

@sales.route('/api/invoices/<int:invoice_id>/lines', methods=['POST'])
@login_required
def api_add_invoice_line(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    if invoice.state != 'draft':
        return jsonify({'error': 'Cannot modify a validated or cancelled invoice'}), 400
    
    data = request.json
    
    # Validate required fields
    if not data.get('product_id') or not data.get('quantity') or not data.get('unit_price'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    product_id = data.get('product_id')
    product = Product.query.get(product_id)
    
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    # Create new invoice line
    line = InvoiceLine(
        invoice_id=invoice_id,
        product_id=product_id,
        description=data.get('description', product.name),
        quantity=data.get('quantity'),
        unit_price=data.get('unit_price'),
        tax_rate=data.get('tax_rate', 0)
    )
    
    # Calculate tax amount and subtotal
    line.subtotal = line.quantity * line.unit_price
    line.tax_amount = line.subtotal * (line.tax_rate / 100)
    
    db.session.add(line)
    db.session.commit()
    
    # Recalculate invoice totals
    invoice.calculate_totals()
    db.session.commit()
    
    return jsonify({
        'id': line.id,
        'product_id': line.product_id,
        'product_name': product.name,
        'description': line.description,
        'quantity': line.quantity,
        'unit_price': float(line.unit_price),
        'tax_rate': float(line.tax_rate),
        'tax_amount': float(line.tax_amount),
        'subtotal': float(line.subtotal),
        'invoice_total': float(invoice.total_amount)
    })

@sales.route('/api/invoice-lines/<int:line_id>', methods=['PUT'])
@login_required
def api_update_invoice_line(line_id):
    line = InvoiceLine.query.get_or_404(line_id)
    invoice = line.invoice
    
    if invoice.state != 'draft':
        return jsonify({'error': 'Cannot modify a validated or cancelled invoice'}), 400
    
    data = request.json
    
    # Update line fields
    if 'product_id' in data and data['product_id'] != line.product_id:
        product = Product.query.get(data['product_id'])
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        line.product_id = data['product_id']
        line.description = product.name
    
    if 'description' in data:
        line.description = data['description']
    
    if 'quantity' in data:
        line.quantity = data['quantity']
    
    if 'unit_price' in data:
        line.unit_price = data['unit_price']
    
    if 'tax_rate' in data:
        line.tax_rate = data['tax_rate']
    
    # Recalculate line totals
    line.subtotal = line.quantity * line.unit_price
    line.tax_amount = line.subtotal * (line.tax_rate / 100)
    
    db.session.commit()
    
    # Recalculate invoice totals
    invoice.calculate_totals()
    db.session.commit()
    
    return jsonify({
        'id': line.id,
        'product_id': line.product_id,
        'product_name': line.product.name if line.product else '',
        'description': line.description,
        'quantity': line.quantity,
        'unit_price': float(line.unit_price),
        'tax_rate': float(line.tax_rate),
        'tax_amount': float(line.tax_amount),
        'subtotal': float(line.subtotal),
        'invoice_total': float(invoice.total_amount)
    })

@sales.route('/api/invoice-lines/<int:line_id>', methods=['DELETE'])
@login_required
def api_delete_invoice_line(line_id):
    line = InvoiceLine.query.get_or_404(line_id)
    invoice = line.invoice
    
    if invoice.state != 'draft':
        return jsonify({'error': 'Cannot modify a validated or cancelled invoice'}), 400
    
    db.session.delete(line)
    db.session.commit()
    
    # Recalculate invoice totals
    invoice.calculate_totals()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'invoice_total': float(invoice.total_amount)
    })

# API endpoints for customer data
@sales.route('/api/customers', methods=['GET'])
@login_required
def api_customers():
    customers = Customer.query.filter_by(is_active=True).all()
    customer_list = []
    
    for customer in customers:
        customer_list.append({
            'id': customer.id,
            'name': customer.name,
            'email': customer.email,
            'phone': customer.phone,
            'address': customer.address
        })
    
    return jsonify(customer_list)

@sales.route('/api/customers/<int:customer_id>', methods=['GET'])
@login_required
def api_customer_details(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    
    # Get open invoices for this customer
    open_invoices = Invoice.query.filter_by(customer_id=customer_id, state='open').all()
    invoice_list = []
    
    for invoice in open_invoices:
        invoice_list.append({
            'id': invoice.id,
            'name': invoice.name,
            'date': invoice.invoice_date.strftime('%Y-%m-%d'),
            'amount_due': float(invoice.amount_due)
        })
    
    # Get recent orders for this customer
    recent_orders = SalesOrder.query.filter_by(customer_id=customer_id).order_by(SalesOrder.order_date.desc()).limit(5).all()
    order_list = []
    
    for order in recent_orders:
        order_list.append({
            'id': order.id,
            'name': order.name,
            'date': order.order_date.strftime('%Y-%m-%d'),
            'amount': float(order.total_amount),
            'state': order.state
        })
    
    return jsonify({
        'id': customer.id,
        'name': customer.name,
        'email': customer.email,
        'phone': customer.phone,
        'address': customer.address,
        'city': customer.city,
        'state': customer.state,
        'zip_code': customer.zip_code,
        'country': customer.country,
        'website': customer.website,
        'tax_id': customer.tax_id,
        'notes': customer.notes,
        'is_active': customer.is_active,
        'open_invoices': invoice_list,
        'recent_orders': order_list
    })

# API endpoints for products
@sales.route('/api/products', methods=['GET'])
@login_required
def api_products():
    products = Product.query.filter_by(is_active=True).all()
    product_list = []
    
    for product in products:
        product_list.append({
            'id': product.id,
            'name': product.name,
            'code': product.code,
            'category': product.category.name if product.category else '',
            'unit_price': float(product.sales_price),
            'available_quantity': product.available_quantity
        })
    
    return jsonify(product_list)

@sales.route('/api/products/<int:product_id>', methods=['GET'])
@login_required
def api_product_details(product_id):
    product = Product.query.get_or_404(product_id)
    
    return jsonify({
        'id': product.id,
        'name': product.name,
        'code': product.code,
        'description': product.description,
        'category_id': product.category_id,
        'category_name': product.category.name if product.category else '',
        'purchase_price': float(product.purchase_price),
        'sales_price': float(product.sales_price),
        'available_quantity': product.available_quantity,
        'is_active': product.is_active
    })

# Invoices
@sales.route('/invoices')
@login_required
def invoices():
    # Get filter parameters
    state_filter = request.args.get('state', '')
    customer_filter = request.args.get('customer_id', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    # Base query
    query = Invoice.query
    
    # Apply filters
    if state_filter:
        query = query.filter(Invoice.state == state_filter)
    
    if customer_filter:
        query = query.filter(Invoice.customer_id == customer_filter)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Invoice.invoice_date >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
            query = query.filter(Invoice.invoice_date <= date_to_obj)
        except ValueError:
            pass
    
    # Get all invoices with applied filters
    invoices = query.order_by(Invoice.invoice_date.desc()).all()
    
    # Get all customers for the filter dropdown
    customers = Customer.query.filter_by(is_active=True).all()
    
    # Calculate totals
    total_amount = sum(invoice.total_amount for invoice in invoices if invoice.state in ['open', 'paid'])
    unpaid_amount = sum(invoice.amount_due for invoice in invoices if invoice.state == 'open')
    
    # Count invoices by state
    draft_count = Invoice.query.filter_by(state='draft').count()
    open_count = Invoice.query.filter_by(state='open').count()
    paid_count = Invoice.query.filter_by(state='paid').count()
    cancelled_count = Invoice.query.filter_by(state='cancelled').count()
    
    return render_template(
        'sales/invoices.html',
        invoices=invoices,
        customers=customers,
        state_filter=state_filter,
        customer_filter=customer_filter,
        date_from=date_from,
        date_to=date_to,
        total_amount=total_amount,
        unpaid_amount=unpaid_amount,
        draft_count=draft_count,
        open_count=open_count,
        paid_count=paid_count,
        cancelled_count=cancelled_count
    )

@sales.route('/invoices/new', methods=['GET', 'POST'])
@login_required
def new_invoice():
    form = InvoiceForm()
    form.customer_id.choices = [(c.id, c.name) for c in Customer.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        # Generate invoice name (e.g., INV0001)
        last_invoice = Invoice.query.order_by(Invoice.id.desc()).first()
        invoice_number = 1
        if last_invoice:
            invoice_number = last_invoice.id + 1
        
        invoice_name = f"INV{invoice_number:04d}"
        
        invoice = Invoice(
            name=invoice_name,
            customer_id=form.customer_id.data,
            invoice_date=form.invoice_date.data,
            due_date=form.due_date.data,
            state='draft',
            notes=form.notes.data,
            created_by=current_user.id,
            created_at=datetime.utcnow()
        )
        
        db.session.add(invoice)
        db.session.commit()
        
        flash('Invoice created successfully!', 'success')
        return redirect(url_for('sales.edit_invoice', invoice_id=invoice.id))
    
    return render_template('sales/invoice_form.html', form=form, title='New Invoice')

@sales.route('/invoices/<int:invoice_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    if invoice.state != 'draft':
        flash('Cannot edit validated or paid invoice.', 'danger')
        return redirect(url_for('sales.invoices'))
    
    form = InvoiceForm(obj=invoice)
    form.customer_id.choices = [(c.id, c.name) for c in Customer.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        invoice.customer_id = form.customer_id.data
        invoice.invoice_date = form.invoice_date.data
        invoice.due_date = form.due_date.data
        invoice.notes = form.notes.data
        
        db.session.commit()
        
        flash('Invoice updated successfully!', 'success')
        return redirect(url_for('sales.edit_invoice', invoice_id=invoice.id))
    
    # Get products for the invoice lines
    products = Product.query.filter_by(is_active=True).all()
    
    return render_template('sales/invoice_edit.html', form=form, invoice=invoice, products=products, title='Edit Invoice')

@sales.route('/invoices/<int:invoice_id>/validate', methods=['POST'])
@login_required
def validate_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    if invoice.state != 'draft':
        flash('Invoice already validated or cancelled.', 'danger')
        return redirect(url_for('sales.invoices'))
    
    if invoice.lines.count() == 0:
        flash('Cannot validate empty invoice.', 'danger')
        return redirect(url_for('sales.edit_invoice', invoice_id=invoice.id))
    
    # Calculate invoice totals
    invoice.calculate_totals()
    invoice.state = 'open'
    db.session.commit()
    
    flash('Invoice validated successfully!', 'success')
    return redirect(url_for('sales.invoices'))

@sales.route('/invoices/<int:invoice_id>/cancel', methods=['POST'])
@login_required
def cancel_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    if invoice.state == 'paid':
        flash('Cannot cancel paid invoice.', 'danger')
        return redirect(url_for('sales.invoices'))
    
    # Cancel related payments
    for payment in invoice.payments:
        payment.state = 'cancelled'
    
    invoice.state = 'cancelled'
    db.session.commit()
    
    flash('Invoice cancelled successfully!', 'success')
    return redirect(url_for('sales.invoices'))

# Payments
@sales.route('/payments')
@login_required
def payments():
    # Get filter parameters
    customer_filter = request.args.get('customer_id', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    invoice_filter = request.args.get('invoice_id', '')
    
    # Base query
    query = Payment.query
    
    # Apply filters
    if customer_filter:
        query = query.join(Invoice).filter(Invoice.customer_id == customer_filter)
    
    if invoice_filter:
        query = query.filter(Payment.invoice_id == invoice_filter)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Payment.payment_date >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
            query = query.filter(Payment.payment_date <= date_to_obj)
        except ValueError:
            pass
    
    # Get all payments with applied filters
    payments = query.order_by(Payment.payment_date.desc()).all()
    
    # Get all customers for the filter dropdown
    customers = Customer.query.filter_by(is_active=True).all()
    
    # Get all open invoices for the filter dropdown
    invoices = Invoice.query.filter_by(state='open').all()
    
    # Calculate total payments
    total_payments = sum(payment.amount for payment in payments)
    
    return render_template(
        'sales/payments.html',
        payments=payments,
        customers=customers,
        invoices=invoices,
        customer_filter=customer_filter,
        date_from=date_from,
        date_to=date_to,
        invoice_filter=invoice_filter,
        total_payments=total_payments
    )

@sales.route('/payments/new/<int:invoice_id>', methods=['GET', 'POST'])
@login_required
def new_payment(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    if invoice.state != 'open':
        flash('Can only register payments for validated invoices.', 'danger')
        return redirect(url_for('sales.invoices'))
    
    form = PaymentForm()
    
    # Set default values
    if request.method == 'GET':
        form.amount.data = invoice.amount_due
    
    if form.validate_on_submit():
        # Generate payment name (e.g., PAY0001)
        last_payment = Payment.query.order_by(Payment.id.desc()).first()
        payment_number = 1
        if last_payment:
            payment_number = last_payment.id + 1
        
        payment_name = f"PAY{payment_number:04d}"
        
        payment = Payment(
            name=payment_name,
            invoice_id=invoice.id,
            payment_date=form.payment_date.data,
            amount=form.amount.data,
            payment_method=form.payment_method.data,
            reference=form.reference.data,
            state='draft',
            notes=form.notes.data,
            created_by=current_user.id,
            created_at=datetime.utcnow()
        )
        
        db.session.add(payment)
        db.session.commit()
        
        # Validate payment
        payment.state = 'posted'
        
        # Check if invoice is fully paid
        if invoice.amount_due <= 0:
            invoice.state = 'paid'
        
        db.session.commit()
        
        flash('Payment registered successfully!', 'success')
        return redirect(url_for('sales.invoices'))
    
    return render_template('sales/payment_form.html', form=form, invoice=invoice, title='Register Payment')

# Reports
@sales.route('/reports')
@login_required
def reports():
    customers = Customer.query.filter_by(is_active=True).all()
    products = Product.query.filter_by(is_active=True).all()
    today = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('sales/reports.html', 
                           customers=customers, 
                           products=products, 
                           today=today)

@sales.route('/reports/sales', methods=['POST'])
@login_required
def generate_sales_report():
    period = request.form.get('period')
    report_format = request.form.get('format')
    include_pos = request.form.get('include_pos', 'yes') == 'yes'
    
    # Calculate date range based on period
    end_date = datetime.now()
    
    if period == 'today':
        start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'yesterday':
        start_date = (end_date - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
    elif period == 'this_week':
        # Start from Monday of current week
        start_date = (end_date - timedelta(days=end_date.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'last_week':
        # Start from Monday of previous week
        start_date = (end_date - timedelta(days=end_date.weekday() + 7)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=7)
    elif period == 'this_month':
        start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == 'last_month':
        if end_date.month == 1:
            start_date = end_date.replace(year=end_date.year-1, month=12, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start_date = end_date.replace(month=end_date.month-1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == 'this_quarter':
        quarter = (end_date.month - 1) // 3 + 1
        start_date = datetime(end_date.year, 3 * quarter - 2, 1)
    elif period == 'last_quarter':
        quarter = (end_date.month - 1) // 3 + 1
        if quarter == 1:
            start_date = datetime(end_date.year - 1, 10, 1)
            end_date = datetime(end_date.year, 1, 1)
        else:
            start_date = datetime(end_date.year, 3 * (quarter - 1) - 2, 1)
            end_date = datetime(end_date.year, 3 * quarter - 2, 1)
    elif period == 'this_year':
        start_date = datetime(end_date.year, 1, 1)
    elif period == 'last_year':
        start_date = datetime(end_date.year - 1, 1, 1)
        end_date = datetime(end_date.year, 1, 1)
    elif period == 'custom':
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d') + timedelta(days=1)
    else:
        flash('Invalid period selected', 'danger')
        return redirect(url_for('sales.reports'))
    
    # Prepare data for the report
    report_data = []
    
    # Query sales orders within the date range
    orders = SalesOrder.query.filter(
        SalesOrder.order_date >= start_date,
        SalesOrder.order_date < end_date,
        SalesOrder.state.in_(['confirmed', 'done'])
    ).order_by(SalesOrder.order_date).all()
    
    # Add sales orders to report data
    for order in orders:
        report_data.append({
            'order_number': order.name,
            'date': order.order_date.strftime('%Y-%m-%d'),
            'customer': order.customer.name,
            'status': order.state,
            'total': order.total_amount,
            'tax': order.tax_amount,
            'grand_total': order.total_amount + order.tax_amount - order.discount_amount,
            'source': 'Sales'
        })
    
    # Include POS orders if requested
    if include_pos:
        from modules.pos.models import POSOrder
        try:
            # Query POS orders within the date range
            pos_orders = POSOrder.query.filter(
                POSOrder.order_date >= start_date,
                POSOrder.order_date < end_date,
                POSOrder.state == 'paid'
            ).order_by(POSOrder.order_date).all()
            
            # Add POS orders to report data
            for order in pos_orders:
                customer_name = "Walk-in Customer"
                if order.customer_id and order.customer:
                    customer_name = order.customer.name
                
                report_data.append({
                    'order_number': order.name,
                    'date': order.order_date.strftime('%Y-%m-%d'),
                    'customer': customer_name,
                    'status': order.state,
                    'total': order.total_amount,
                    'tax': order.tax_amount,
                    'grand_total': order.total_amount + order.tax_amount - order.discount_amount,
                    'source': 'POS'
                })
        except Exception as e:
            flash(f'Error including POS orders: {str(e)}', 'warning')
    
    # Sort combined data by date
    report_data.sort(key=lambda x: x['date'])
    
    # Generate report based on format
    if report_format == 'csv':
        return generate_csv_report(report_data, f"Sales_Report_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.csv")
    elif report_format == 'excel':
        flash('Excel report generation is not available yet', 'warning')
        return redirect(url_for('sales.reports'))
    elif report_format == 'pdf':
        flash('PDF report generation is not available yet', 'warning')
        return redirect(url_for('sales.reports'))
    else:
        flash('Invalid report format selected', 'danger')
        return redirect(url_for('sales.reports'))

@sales.route('/reports/customer', methods=['POST'])
@login_required
def generate_customer_report():
    customer_id = request.form.get('customer_id')
    period = request.form.get('period')
    report_format = request.form.get('format')
    include_pos = request.form.get('include_pos', 'yes') == 'yes'
    
    # Calculate date range based on period
    end_date = datetime.now()
    
    if period == 'this_month':
        start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == 'last_month':
        if end_date.month == 1:
            start_date = end_date.replace(year=end_date.year-1, month=12, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start_date = end_date.replace(month=end_date.month-1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == 'this_quarter':
        quarter = (end_date.month - 1) // 3 + 1
        start_date = datetime(end_date.year, 3 * quarter - 2, 1)
    elif period == 'last_quarter':
        quarter = (end_date.month - 1) // 3 + 1
        if quarter == 1:
            start_date = datetime(end_date.year - 1, 10, 1)
            end_date = datetime(end_date.year, 1, 1)
        else:
            start_date = datetime(end_date.year, 3 * (quarter - 1) - 2, 1)
            end_date = datetime(end_date.year, 3 * quarter - 2, 1)
    elif period == 'this_year':
        start_date = datetime(end_date.year, 1, 1)
    elif period == 'last_year':
        start_date = datetime(end_date.year - 1, 1, 1)
        end_date = datetime(end_date.year, 1, 1)
    elif period == 'all_time':
        start_date = datetime(2000, 1, 1)  # A date far in the past
    elif period == 'custom':
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d') + timedelta(days=1)
    else:
        flash('Invalid period selected', 'danger')
        return redirect(url_for('sales.reports'))
    
    # Prepare data for the report
    report_data = []
    
    # Build query for sales orders
    query = SalesOrder.query.filter(
        SalesOrder.order_date >= start_date,
        SalesOrder.order_date < end_date,
        SalesOrder.state.in_(['confirmed', 'done'])
    )
    
    # Filter by customer if specified
    if customer_id != 'all':
        query = query.filter(SalesOrder.customer_id == customer_id)
    
    # Get orders
    orders = query.order_by(SalesOrder.customer_id, SalesOrder.order_date).all()
    
    # Add sales orders to report data
    for order in orders:
        report_data.append({
            'customer': order.customer.name,
            'order_number': order.name,
            'date': order.order_date.strftime('%Y-%m-%d'),
            'status': order.state,
            'total': order.total_amount,
            'tax': order.tax_amount,
            'grand_total': order.total_amount + order.tax_amount - order.discount_amount,
            'source': 'Sales'
        })
    
    # Include POS orders if requested
    if include_pos:
        from modules.pos.models import POSOrder
        try:
            # Build query for POS orders
            pos_query = POSOrder.query.filter(
                POSOrder.order_date >= start_date,
                POSOrder.order_date < end_date,
                POSOrder.state == 'paid'
            )
            
            # Filter by customer if specified
            if customer_id != 'all':
                pos_query = pos_query.filter(POSOrder.customer_id == customer_id)
            
            # Get POS orders
            pos_orders = pos_query.order_by(POSOrder.customer_id, POSOrder.order_date).all()
            
            # Add POS orders to report data
            for order in pos_orders:
                customer_name = "Walk-in Customer"
                if order.customer_id and order.customer:
                    customer_name = order.customer.name
                
                report_data.append({
                    'customer': customer_name,
                    'order_number': order.name,
                    'date': order.order_date.strftime('%Y-%m-%d'),
                    'status': order.state,
                    'total': order.total_amount,
                    'tax': order.tax_amount,
                    'grand_total': order.total_amount + order.tax_amount - order.discount_amount,
                    'source': 'POS'
                })
        except Exception as e:
            flash(f'Error including POS orders: {str(e)}', 'warning')
    
    # Sort combined data by customer and date
    report_data.sort(key=lambda x: (x['customer'], x['date']))
    
    # Generate report based on format
    report_name = "Customer_Sales_Report"
    if customer_id != 'all':
        customer = Customer.query.get(customer_id)
        if customer:
            report_name = f"{customer.name}_Sales_Report"
    
    if report_format == 'csv':
        return generate_csv_report(report_data, f"{report_name}_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.csv")
    elif report_format == 'excel':
        flash('Excel report generation is not available yet', 'warning')
        return redirect(url_for('sales.reports'))
    elif report_format == 'pdf':
        flash('PDF report generation is not available yet', 'warning')
        return redirect(url_for('sales.reports'))
    else:
        flash('Invalid report format selected', 'danger')
        return redirect(url_for('sales.reports'))

@sales.route('/reports/product', methods=['POST'])
@login_required
def generate_product_report():
    product_id = request.form.get('product_id')
    period = request.form.get('period')
    report_format = request.form.get('format')
    include_pos = request.form.get('include_pos', 'yes') == 'yes'
    
    # Calculate date range based on period
    end_date = datetime.now()
    
    if period == 'this_month':
        start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == 'last_month':
        if end_date.month == 1:
            start_date = end_date.replace(year=end_date.year-1, month=12, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start_date = end_date.replace(month=end_date.month-1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == 'this_quarter':
        quarter = (end_date.month - 1) // 3 + 1
        start_date = datetime(end_date.year, 3 * quarter - 2, 1)
    elif period == 'last_quarter':
        quarter = (end_date.month - 1) // 3 + 1
        if quarter == 1:
            start_date = datetime(end_date.year - 1, 10, 1)
            end_date = datetime(end_date.year, 1, 1)
        else:
            start_date = datetime(end_date.year, 3 * (quarter - 1) - 2, 1)
            end_date = datetime(end_date.year, 3 * quarter - 2, 1)
    elif period == 'this_year':
        start_date = datetime(end_date.year, 1, 1)
    elif period == 'last_year':
        start_date = datetime(end_date.year - 1, 1, 1)
        end_date = datetime(end_date.year, 1, 1)
    elif period == 'all_time':
        start_date = datetime(2000, 1, 1)  # A date far in the past
    elif period == 'custom':
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d') + timedelta(days=1)
    else:
        flash('Invalid period selected', 'danger')
        return redirect(url_for('sales.reports'))
    
    # Prepare data for the report
    report_data = []
    
    # Build query for sales order lines
    query = db.session.query(
        SalesOrderLine, SalesOrder, Product
    ).join(
        SalesOrder, SalesOrderLine.order_id == SalesOrder.id
    ).join(
        Product, SalesOrderLine.product_id == Product.id
    ).filter(
        SalesOrder.order_date >= start_date,
        SalesOrder.order_date < end_date,
        SalesOrder.state.in_(['confirmed', 'done'])
    )
    
    # Filter by product if specified
    if product_id != 'all':
        query = query.filter(SalesOrderLine.product_id == product_id)
    
    # Get order lines
    results = query.order_by(Product.name, SalesOrder.order_date).all()
    
    # Add sales order lines to report data
    for line, order, product in results:
        report_data.append({
            'product': product.name,
            'order_number': order.name,
            'date': order.order_date.strftime('%Y-%m-%d'),
            'customer': order.customer.name,
            'quantity': line.quantity,
            'unit_price': line.unit_price,
            'subtotal': line.subtotal,
            'source': 'Sales'
        })
    
    # Include POS orders if requested
    if include_pos:
        from modules.pos.models import POSOrderLine
        try:
            # Build query for POS order lines
            pos_query = db.session.query(
                POSOrderLine, POSOrder, Product
            ).join(
                POSOrder, POSOrderLine.order_id == POSOrder.id
            ).join(
                Product, POSOrderLine.product_id == Product.id
            ).filter(
                POSOrder.order_date >= start_date,
                POSOrder.order_date < end_date,
                POSOrder.state == 'paid'
            )
            
            # Filter by product if specified
            if product_id != 'all':
                pos_query = pos_query.filter(POSOrderLine.product_id == product_id)
            
            # Get POS order lines
            pos_results = pos_query.order_by(Product.name, POSOrder.order_date).all()
            
            # Add POS order lines to report data
            for line, order, product in pos_results:
                customer_name = "Walk-in Customer"
                if order.customer_id and order.customer:
                    customer_name = order.customer.name
                
                report_data.append({
                    'product': product.name,
                    'order_number': order.name,
                    'date': order.order_date.strftime('%Y-%m-%d'),
                    'customer': customer_name,
                    'quantity': line.quantity,
                    'unit_price': line.unit_price,
                    'subtotal': line.subtotal,
                    'source': 'POS'
                })
        except Exception as e:
            flash(f'Error including POS orders: {str(e)}', 'warning')
    
    # Sort combined data by product and date
    report_data.sort(key=lambda x: (x['product'], x['date']))
    
    # Generate report based on format
    report_name = "Product_Sales_Report"
    if product_id != 'all':
        product = Product.query.get(product_id)
        if product:
            report_name = f"{product.name}_Sales_Report"
    
    if report_format == 'csv':
        return generate_csv_report(report_data, f"{report_name}_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.csv")
    elif report_format == 'excel':
        flash('Excel report generation is not available yet', 'warning')
        return redirect(url_for('sales.reports'))
    elif report_format == 'pdf':
        flash('PDF report generation is not available yet', 'warning')
        return redirect(url_for('sales.reports'))
    else:
        flash('Invalid report format selected', 'danger')
        return redirect(url_for('sales.reports'))

@sales.route('/reports/payment', methods=['POST'])
@login_required
def generate_payment_report():
    payment_method = request.form.get('payment_method')
    period = request.form.get('period')
    report_format = request.form.get('format')
    
    # Calculate date range based on period
    end_date = datetime.now()
    
    if period == 'this_month':
        start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == 'last_month':
        if end_date.month == 1:
            start_date = end_date.replace(year=end_date.year-1, month=12, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start_date = end_date.replace(month=end_date.month-1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == 'this_quarter':
        quarter = (end_date.month - 1) // 3 + 1
        start_date = datetime(end_date.year, 3 * quarter - 2, 1)
    elif period == 'last_quarter':
        quarter = (end_date.month - 1) // 3 + 1
        if quarter == 1:
            start_date = datetime(end_date.year - 1, 10, 1)
            end_date = datetime(end_date.year, 1, 1)
        else:
            start_date = datetime(end_date.year, 3 * (quarter - 1) - 2, 1)
            end_date = datetime(end_date.year, 3 * quarter - 2, 1)
    elif period == 'this_year':
        start_date = datetime(end_date.year, 1, 1)
    elif period == 'last_year':
        start_date = datetime(end_date.year - 1, 1, 1)
        end_date = datetime(end_date.year, 1, 1)
    elif period == 'all_time':
        start_date = datetime(2000, 1, 1)  # A date far in the past
    elif period == 'custom':
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d') + timedelta(days=1)
    else:
        flash('Invalid period selected', 'danger')
        return redirect(url_for('sales.reports'))
    
    # Build query for payments
    query = db.session.query(
        Payment, Invoice, Customer
    ).join(
        Invoice, Payment.invoice_id == Invoice.id
    ).join(
        Customer, Invoice.customer_id == Customer.id
    ).filter(
        Payment.payment_date >= start_date,
        Payment.payment_date < end_date
    )
    
    # Filter by payment method if specified
    if payment_method != 'all':
        query = query.filter(Payment.payment_method == payment_method)
    
    # Get payments
    results = query.order_by(Payment.payment_date).all()
    
    # Prepare data for the report
    report_data = []
    for payment, invoice, customer in results:
        report_data.append({
            'date': payment.payment_date.strftime('%Y-%m-%d'),
            'invoice': invoice.name,
            'customer': customer.name,
            'method': payment.payment_method,
            'reference': payment.reference or '',
            'amount': payment.amount
        })
    
    # Generate report based on format
    report_name = "Payment_Collection_Report"
    if payment_method != 'all':
        report_name = f"{payment_method.capitalize()}_Payment_Report"
    
    if report_format == 'csv':
        return generate_csv_report(report_data, f"{report_name}_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.csv")
    elif report_format == 'excel':
        flash('Excel report generation is not available yet', 'warning')
        return redirect(url_for('sales.reports'))
    elif report_format == 'pdf':
        flash('PDF report generation is not available yet', 'warning')
        return redirect(url_for('sales.reports'))
    else:
        flash('Invalid report format selected', 'danger')
        return redirect(url_for('sales.reports'))

@sales.route('/reports/aging', methods=['POST'])
@login_required
def generate_aging_report():
    customer_id = request.form.get('customer_id')
    as_of_date_str = request.form.get('as_of_date')
    aging_buckets = request.form.get('aging_buckets')
    report_format = request.form.get('format')
    
    # Parse as of date
    try:
        as_of_date = datetime.strptime(as_of_date_str, '%Y-%m-%d')
    except ValueError:
        as_of_date = datetime.now()
    
    # Determine aging buckets
    if aging_buckets == '30_60_90':
        bucket_days = [30, 60, 90]
    elif aging_buckets == '7_14_30_60':
        bucket_days = [7, 14, 30, 60]
    elif aging_buckets == 'custom':
        try:
            bucket_days = [int(days.strip()) for days in request.form.get('custom_buckets').split(',')]
            bucket_days.sort()  # Ensure days are in ascending order
        except:
            flash('Invalid custom aging buckets', 'danger')
            return redirect(url_for('sales.reports'))
    else:
        bucket_days = [30, 60, 90]  # Default
    
    # Build query for open invoices
    query = db.session.query(
        Invoice, Customer
    ).join(
        Customer, Invoice.customer_id == Customer.id
    ).filter(
        Invoice.state == 'open',
        Invoice.invoice_date <= as_of_date
    )
    
    # Filter by customer if specified
    if customer_id != 'all':
        query = query.filter(Invoice.customer_id == customer_id)
    
    # Get invoices
    results = query.order_by(Customer.name, Invoice.due_date).all()
    
    # Prepare data for the report
    report_data = []
    for invoice, customer in results:
        # Calculate days overdue
        days_overdue = (as_of_date - invoice.due_date).days if as_of_date > invoice.due_date else 0
        
        # Determine aging bucket
        bucket = 'Current'
        if days_overdue > 0:
            for i, days in enumerate(bucket_days):
                if days_overdue <= days:
                    bucket = f"1-{days} days"
                    break
                elif i == len(bucket_days) - 1:
                    bucket = f">{days} days"
        
        report_data.append({
            'customer': customer.name,
            'invoice': invoice.name,
            'date': invoice.invoice_date.strftime('%Y-%m-%d'),
            'due_date': invoice.due_date.strftime('%Y-%m-%d'),
            'days_overdue': days_overdue,
            'aging_bucket': bucket,
            'amount_due': invoice.amount_due
        })
    
    # Generate report based on format
    report_name = "Accounts_Receivable_Aging_Report"
    if customer_id != 'all':
        customer = Customer.query.get(customer_id)
        if customer:
            report_name = f"{customer.name}_Aging_Report"
    
    if report_format == 'csv':
        return generate_csv_report(report_data, f"{report_name}_{as_of_date.strftime('%Y%m%d')}.csv")
    elif report_format == 'excel':
        flash('Excel report generation is not available yet', 'warning')
        return redirect(url_for('sales.reports'))
    elif report_format == 'pdf':
        flash('PDF report generation is not available yet', 'warning')
        return redirect(url_for('sales.reports'))
    else:
        flash('Invalid report format selected', 'danger')
        return redirect(url_for('sales.reports'))

# Helper function for CSV report generation
def generate_csv_report(data, filename):
    if not data:
        flash('No data available for the report', 'warning')
        return redirect(url_for('sales.reports'))
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    
    # Create response
    response = send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )
    
    return response
