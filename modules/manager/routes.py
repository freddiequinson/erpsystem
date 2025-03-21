from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date
import calendar
from sqlalchemy import func, desc
from functools import wraps

from modules.auth.models import User, Role, UserRole
from modules.pos.models import POSOrder, POSOrderLine, POSSession, POSPaymentMethod, POSReturn
from modules.inventory.models import Product, StockMove
from app import db

# Create a blueprint for the manager module
manager_bp = Blueprint('manager', __name__, url_prefix='/manager')

# Create a decorator to check if user has manager role
def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user has manager role
        manager_role = Role.query.filter_by(name='Manager').first()
        admin_role = Role.query.filter_by(name='Admin').first()
        
        if not manager_role or not admin_role:
            flash('Role configuration error.', 'danger')
            return redirect(url_for('auth.login'))
        
        if manager_role not in current_user.roles and admin_role not in current_user.roles:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard.index'))
            
        return f(*args, **kwargs)
    return decorated_function

# Manager dashboard
@manager_bp.route('/')
@login_required
@manager_required
def dashboard():
    # Get today's date
    today = datetime.now().date()
    
    # Calculate today's sales
    today_sales_query = db.session.query(func.sum(POSOrder.total_amount)).filter(
        func.date(POSOrder.order_date) == today,
        POSOrder.state == 'paid'
    ).scalar()
    today_sales = today_sales_query if today_sales_query else 0
    
    # Calculate today's orders
    today_orders = POSOrder.query.filter(
        func.date(POSOrder.order_date) == today,
        POSOrder.state == 'paid'
    ).count()
    
    # Get active sessions
    active_sessions = POSSession.query.join(User).filter(
        POSSession.state == 'opened'
    ).count()
    
    # Get sales staff (users with Cashier role)
    cashier_role = Role.query.filter_by(name='Cashier').first()
    sales_staff = []
    
    if cashier_role:
        staff_users = User.query.join(UserRole).join(Role).filter(
            Role.name == 'Cashier'
        ).all()
        
        for user in staff_users:
            # Calculate today's sales for this user
            user_sales = db.session.query(func.sum(POSOrder.total_amount)).filter(
                func.date(POSOrder.order_date) == today,
                POSOrder.state == 'paid',
                POSOrder.user_id == user.id
            ).scalar() or 0
            
            # Calculate today's orders for this user
            user_orders = POSOrder.query.filter(
                func.date(POSOrder.order_date) == today,
                POSOrder.state == 'paid',
                POSOrder.user_id == user.id
            ).count()
            
            # Check if user has active session
            active_session = POSSession.query.filter_by(
                user_id=user.id,
                state='opened'
            ).first() is not None
            
            sales_staff.append({
                'id': user.id,
                'username': user.username,
                'today_sales': user_sales,
                'today_orders': user_orders,
                'active_session': active_session
            })
    
    # Get recent orders
    recent_orders = POSOrder.query.order_by(POSOrder.order_date.desc()).limit(10).all()
    
    return render_template('manager/dashboard.html',
                          today_sales=today_sales,
                          today_orders=today_orders,
                          active_sessions=active_sessions,
                          sales_staff=sales_staff,
                          recent_orders=recent_orders)

# Staff details
@manager_bp.route('/staff/<int:user_id>')
@login_required
@manager_required
def staff_details(user_id):
    # Get the staff user
    staff = User.query.get_or_404(user_id)
    
    # Get today's date
    today = datetime.now().date()
    
    # Calculate sales statistics
    today_sales = db.session.query(func.sum(POSOrder.total_amount)).filter(
        func.date(POSOrder.order_date) == today,
        POSOrder.state == 'paid',
        POSOrder.user_id == user_id
    ).scalar() or 0
    
    # Calculate week sales
    week_start = today - timedelta(days=today.weekday())
    week_sales = db.session.query(func.sum(POSOrder.total_amount)).filter(
        func.date(POSOrder.order_date) >= week_start,
        func.date(POSOrder.order_date) <= today,
        POSOrder.state == 'paid',
        POSOrder.user_id == user_id
    ).scalar() or 0
    
    # Calculate month sales
    month_start = date(today.year, today.month, 1)
    month_sales = db.session.query(func.sum(POSOrder.total_amount)).filter(
        func.date(POSOrder.order_date) >= month_start,
        func.date(POSOrder.order_date) <= today,
        POSOrder.state == 'paid',
        POSOrder.user_id == user_id
    ).scalar() or 0
    
    # Calculate today's orders
    today_orders = POSOrder.query.filter(
        func.date(POSOrder.order_date) == today,
        POSOrder.state == 'paid',
        POSOrder.user_id == user_id
    ).count()
    
    # Get recent orders
    recent_orders = POSOrder.query.filter_by(
        user_id=user_id
    ).order_by(POSOrder.order_date.desc()).limit(10).all()
    
    # Get session history
    sessions = POSSession.query.filter_by(
        user_id=user_id
    ).order_by(POSSession.start_time.desc()).limit(10).all()
    
    # Calculate daily performance for the last 14 days
    daily_performance = []
    sales_dates = []
    sales_amounts = []
    
    for i in range(13, -1, -1):
        day_date = today - timedelta(days=i)
        day_sales = db.session.query(func.sum(POSOrder.total_amount)).filter(
            func.date(POSOrder.order_date) == day_date,
            POSOrder.state == 'paid',
            POSOrder.user_id == user_id
        ).scalar() or 0
        
        day_orders = POSOrder.query.filter(
            func.date(POSOrder.order_date) == day_date,
            POSOrder.state == 'paid',
            POSOrder.user_id == user_id
        ).count()
        
        day_average = day_sales / day_orders if day_orders > 0 else 0
        
        daily_performance.append({
            'date': day_date,
            'sales': day_sales,
            'orders': day_orders,
            'average': day_average
        })
        
        sales_dates.append(day_date.strftime('%Y-%m-%d'))
        sales_amounts.append(day_sales)
    
    # Get top products sold by this user
    top_products_query = db.session.query(
        Product.id,
        Product.name,
        func.sum(POSOrderLine.qty).label('quantity'),
        func.sum(POSOrderLine.price_subtotal).label('sales')
    ).join(
        POSOrderLine, POSOrderLine.product_id == Product.id
    ).join(
        POSOrder, POSOrder.id == POSOrderLine.order_id
    ).filter(
        POSOrder.user_id == user_id,
        POSOrder.state == 'paid'
    ).group_by(
        Product.id
    ).order_by(
        func.sum(POSOrderLine.price_subtotal).desc()
    ).limit(10).all()
    
    top_products = []
    product_names = []
    product_sales = []
    total_product_sales = sum(product.sales for product in top_products_query)
    
    for product in top_products_query:
        percentage = (product.sales / total_product_sales * 100) if total_product_sales > 0 else 0
        top_products.append({
            'name': product.name,
            'quantity': product.quantity,
            'sales': product.sales,
            'percentage': percentage
        })
        product_names.append(product.name)
        product_sales.append(product.sales)
    
    return render_template('manager/staff_details.html',
                          staff=staff,
                          today_sales=today_sales,
                          week_sales=week_sales,
                          month_sales=month_sales,
                          today_orders=today_orders,
                          recent_orders=recent_orders,
                          sessions=sessions,
                          daily_performance=daily_performance,
                          top_products=top_products,
                          sales_dates=sales_dates,
                          sales_amounts=sales_amounts,
                          product_names=product_names,
                          product_sales=product_sales,
                          now=datetime.now())

# Staff performance
@manager_bp.route('/staff-performance')
@login_required
@manager_required
def staff_performance():
    # Get filter parameters
    date_range = request.args.get('date_range', 'this_month')
    metric = request.args.get('metric', 'sales_amount')
    
    # Calculate date range
    today = datetime.now().date()
    
    if date_range == 'today':
        start_date = today
        end_date = today
    elif date_range == 'yesterday':
        start_date = today - timedelta(days=1)
        end_date = today - timedelta(days=1)
    elif date_range == 'this_week':
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif date_range == 'last_week':
        start_date = today - timedelta(days=today.weekday() + 7)
        end_date = today - timedelta(days=today.weekday() + 1)
    elif date_range == 'this_month':
        start_date = date(today.year, today.month, 1)
        end_date = today
    elif date_range == 'last_month':
        if today.month == 1:
            start_date = date(today.year - 1, 12, 1)
            end_date = date(today.year, 1, 1) - timedelta(days=1)
        else:
            start_date = date(today.year, today.month - 1, 1)
            end_date = date(today.year, today.month, 1) - timedelta(days=1)
    elif date_range == 'custom':
        try:
            start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            start_date = date(today.year, today.month, 1)
            end_date = today
    else:
        start_date = date(today.year, today.month, 1)
        end_date = today
    
    # Get all users who have created POS orders
    user_ids_with_orders = db.session.query(POSOrder.created_by).distinct().filter(
        POSOrder.created_by.isnot(None),
        func.date(POSOrder.order_date) >= start_date,
        func.date(POSOrder.order_date) <= end_date,
        POSOrder.state == 'paid'
    ).all()
    
    user_ids = [user_id[0] for user_id in user_ids_with_orders]
    
    # Then get the user objects
    staff_users = User.query.filter(User.id.in_(user_ids)).all()
    
    # If no users found with orders, fallback to users with Cashier role
    cashier_role = Role.query.filter_by(name='Cashier').first()
    if not staff_users and cashier_role:
        staff_users = User.query.join(UserRole).join(Role).filter(
            Role.name == 'Cashier'
        ).all()
    
    staff_performance = []
    staff_names = []
    performance_data = []
    
    for user in staff_users:
        # Calculate sales amount
        sales_amount = db.session.query(func.sum(POSOrder.total_amount)).filter(
            func.date(POSOrder.order_date) >= start_date,
            func.date(POSOrder.order_date) <= end_date,
            POSOrder.state == 'paid',
            POSOrder.created_by == user.id
        ).scalar() or 0
        
        # Calculate order count
        order_count = POSOrder.query.filter(
            func.date(POSOrder.order_date) >= start_date,
            func.date(POSOrder.order_date) <= end_date,
            POSOrder.state == 'paid',
            POSOrder.created_by == user.id
        ).count()
        
        # Calculate items sold
        items_sold = db.session.query(func.sum(POSOrderLine.quantity)).join(
            POSOrder, POSOrder.id == POSOrderLine.order_id
        ).filter(
            func.date(POSOrder.order_date) >= start_date,
            func.date(POSOrder.order_date) <= end_date,
            POSOrder.state == 'paid',
            POSOrder.created_by == user.id
        ).scalar() or 0
        
        # Calculate average order value
        average_order = sales_amount / order_count if order_count > 0 else 0
        
        staff_performance.append({
            'id': user.id,
            'username': user.username,
            'sales_amount': sales_amount,
            'order_count': order_count,
            'items_sold': items_sold,
            'average_order': average_order
        })
        
        staff_names.append(user.username)
        
        if metric == 'sales_amount':
            performance_data.append(sales_amount)
        elif metric == 'order_count':
            performance_data.append(order_count)
        elif metric == 'average_order':
            performance_data.append(average_order)
        elif metric == 'items_sold':
            performance_data.append(items_sold)
    
    # Sort staff performance by the selected metric
    if metric == 'sales_amount':
        staff_performance.sort(key=lambda x: x['sales_amount'], reverse=True)
        metric_label = 'Sales Amount (₵)'
    elif metric == 'order_count':
        staff_performance.sort(key=lambda x: x['order_count'], reverse=True)
        metric_label = 'Order Count'
    elif metric == 'average_order':
        staff_performance.sort(key=lambda x: x['average_order'], reverse=True)
        metric_label = 'Average Order Value (₵)'
    elif metric == 'items_sold':
        staff_performance.sort(key=lambda x: x['items_sold'], reverse=True)
        metric_label = 'Items Sold'
    
    # Calculate totals
    total_sales = sum(staff['sales_amount'] for staff in staff_performance)
    total_orders = sum(staff['order_count'] for staff in staff_performance)
    total_items_sold = sum(staff['items_sold'] for staff in staff_performance)
    average_order_value = total_sales / total_orders if total_orders > 0 else 0
    
    # Get top performers
    top_sales_staff = sorted(staff_performance, key=lambda x: x['sales_amount'], reverse=True)[:5]
    top_orders_staff = sorted(staff_performance, key=lambda x: x['order_count'], reverse=True)[:5]
    
    # Mock data for staff targets
    staff_targets = []
    for staff in staff_performance:
        # Set mock targets based on performance
        sales_target = staff['sales_amount'] * 1.2  # 20% higher than current
        orders_target = staff['order_count'] * 1.2  # 20% higher than current
        
        staff_targets.append({
            'username': staff['username'],
            'sales_amount': staff['sales_amount'],
            'sales_target': sales_target,
            'order_count': staff['order_count'],
            'orders_target': int(orders_target)
        })
    
    return render_template('manager/staff_performance.html',
                          date_range=date_range,
                          start_date=start_date.strftime('%Y-%m-%d'),
                          end_date=end_date.strftime('%Y-%m-%d'),
                          metric=metric,
                          metric_label=metric_label,
                          staff_performance=staff_performance,
                          staff_names=staff_names,
                          performance_data=performance_data,
                          total_sales=total_sales,
                          total_orders=total_orders,
                          total_items_sold=total_items_sold,
                          average_order_value=average_order_value,
                          top_sales_staff=top_sales_staff,
                          top_orders_staff=top_orders_staff,
                          staff_targets=staff_targets)

# Shift management
@manager_bp.route('/shift-management')
@login_required
@manager_required
def shift_management():
    # Get year and month from query parameters or use current date
    year = int(request.args.get('year', datetime.now().year))
    month = int(request.args.get('month', datetime.now().month))
    
    # Create calendar data
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    
    # Get previous and next month
    if month == 1:
        prev_month = 12
        prev_month_year = year - 1
    else:
        prev_month = month - 1
        prev_month_year = year
    
    if month == 12:
        next_month = 1
        next_month_year = year + 1
    else:
        next_month = month + 1
        next_month_year = year
    
    # Get current date for highlighting today
    today = datetime.now().date()
    current_year = today.year
    current_month = today.month
    current_day = today.day
    
    # Mock data for calendar shifts
    calendar_data = []
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                # Day outside of month
                week_data.append({
                    'day': '',
                    'in_month': False,
                    'is_today': False,
                    'shifts': []
                })
            else:
                # Check if this day is today
                is_today = (year == today.year and month == today.month and day == today.day)
                
                # Check if this day is in the past
                day_date = date(year, month, day)
                in_past = day_date < today
                
                # Mock shifts for this day (in a real app, these would come from the database)
                shifts = []
                if not in_past and day % 3 == 0:
                    shifts.append({
                        'staff_name': 'John Doe',
                        'type': 'morning',
                        'start_time': '08:00',
                        'end_time': '12:00'
                    })
                
                if not in_past and day % 4 == 0:
                    shifts.append({
                        'staff_name': 'Jane Smith',
                        'type': 'afternoon',
                        'start_time': '12:00',
                        'end_time': '16:00'
                    })
                
                if not in_past and day % 5 == 0:
                    shifts.append({
                        'staff_name': 'Bob Johnson',
                        'type': 'evening',
                        'start_time': '16:00',
                        'end_time': '20:00'
                    })
                
                week_data.append({
                    'day': day,
                    'in_month': True,
                    'is_today': is_today,
                    'in_past': in_past,
                    'shifts': shifts
                })
        
        calendar_data.append(week_data)
    
    # Mock data for upcoming shifts
    upcoming_shifts = []
    for i in range(1, 11):
        shift_date = today + timedelta(days=i)
        
        if i % 2 == 0:
            shift_type = 'morning'
            start_time = datetime.combine(shift_date, datetime.min.time().replace(hour=8))
            end_time = datetime.combine(shift_date, datetime.min.time().replace(hour=12))
        elif i % 3 == 0:
            shift_type = 'afternoon'
            start_time = datetime.combine(shift_date, datetime.min.time().replace(hour=12))
            end_time = datetime.combine(shift_date, datetime.min.time().replace(hour=16))
        else:
            shift_type = 'evening'
            start_time = datetime.combine(shift_date, datetime.min.time().replace(hour=16))
            end_time = datetime.combine(shift_date, datetime.min.time().replace(hour=20))
        
        # Alternate between staff members
        if i % 3 == 0:
            staff_id = 1
            staff_username = 'John Doe'
        elif i % 3 == 1:
            staff_id = 2
            staff_username = 'Jane Smith'
        else:
            staff_id = 3
            staff_username = 'Bob Johnson'
        
        upcoming_shifts.append({
            'id': i,
            'staff': {
                'id': staff_id,
                'username': staff_username
            },
            'date': shift_date,
            'shift_type': shift_type,
            'start_time': start_time,
            'end_time': end_time
        })
    
    # Get staff members for the form
    staff_members = User.query.join(UserRole).join(Role).filter(
        Role.name == 'Cashier'
    ).all()
    
    return render_template('manager/shift_management.html',
                          year=year,
                          month=month,
                          month_name=month_name,
                          calendar_data=calendar_data,
                          prev_month=prev_month,
                          prev_month_year=prev_month_year,
                          next_month=next_month,
                          next_month_year=next_month_year,
                          current_year=current_year,
                          current_month=current_month,
                          current_day=current_day,
                          upcoming_shifts=upcoming_shifts,
                          staff_members=staff_members)

# Add shift (GET - form)
@manager_bp.route('/add-shift')
@login_required
@manager_required
def add_shift():
    # In a real app, this would show a form to add a shift
    # For now, we'll just redirect to the shift management page
    flash('Shift management form would be shown here.', 'info')
    return redirect(url_for('manager.shift_management'))

# Add shift (POST - submit)
@manager_bp.route('/add-shift', methods=['POST'])
@login_required
@manager_required
def add_shift_post():
    # In a real app, this would process the form and add a shift
    # For now, we'll just redirect to the shift management page
    flash('Shift added successfully.', 'success')
    return redirect(url_for('manager.shift_management'))

# Edit shift
@manager_bp.route('/edit-shift/<int:shift_id>')
@login_required
@manager_required
def edit_shift(shift_id):
    # In a real app, this would show a form to edit a shift
    # For now, we'll just redirect to the shift management page
    flash(f'Edit shift form for shift #{shift_id} would be shown here.', 'info')
    return redirect(url_for('manager.shift_management'))

# Delete shift
@manager_bp.route('/delete-shift/<int:shift_id>')
@login_required
@manager_required
def delete_shift(shift_id):
    # In a real app, this would delete a shift
    # For now, we'll just redirect to the shift management page
    flash(f'Shift #{shift_id} deleted successfully.', 'success')
    return redirect(url_for('manager.shift_management'))

# Employee reports
@manager_bp.route('/employee-reports')
@login_required
@manager_required
def employee_reports():
    # Get filter parameters
    date_range = request.args.get('date_range', 'this_month')
    report_type = request.args.get('report_type', 'sales')
    
    # Calculate date range
    today = datetime.now().date()
    
    if date_range == 'today':
        start_date = today
        end_date = today
        date_label = 'Today'
    elif date_range == 'yesterday':
        start_date = today - timedelta(days=1)
        end_date = today - timedelta(days=1)
        date_label = 'Yesterday'
    elif date_range == 'this_week':
        start_date = today - timedelta(days=today.weekday())
        end_date = today
        date_label = 'This Week'
    elif date_range == 'last_week':
        start_date = today - timedelta(days=today.weekday() + 7)
        end_date = today - timedelta(days=today.weekday() + 1)
        date_label = 'Last Week'
    elif date_range == 'this_month':
        start_date = date(today.year, today.month, 1)
        end_date = today
        date_label = f'{calendar.month_name[today.month]} {today.year}'
    elif date_range == 'last_month':
        if today.month == 1:
            start_date = date(today.year - 1, 12, 1)
            end_date = date(today.year, 1, 1) - timedelta(days=1)
            date_label = f'December {today.year - 1}'
        else:
            start_date = date(today.year, today.month - 1, 1)
            end_date = date(today.year, today.month, 1) - timedelta(days=1)
            date_label = f'{calendar.month_name[today.month - 1]} {today.year}'
    elif date_range == 'custom':
        try:
            start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
            date_label = f'{start_date.strftime("%b %d, %Y")} to {end_date.strftime("%b %d, %Y")}'
        except (ValueError, TypeError):
            start_date = date(today.year, today.month, 1)
            end_date = today
            date_label = f'{calendar.month_name[today.month]} {today.year}'
    else:
        start_date = date(today.year, today.month, 1)
        end_date = today
        date_label = f'{calendar.month_name[today.month]} {today.year}'
    
    # Get all users who have created POS orders
    user_ids_with_orders = db.session.query(POSOrder.created_by).distinct().filter(
        POSOrder.created_by.isnot(None),
        func.date(POSOrder.order_date) >= start_date,
        func.date(POSOrder.order_date) <= end_date,
        POSOrder.state == 'paid'
    ).all()
    
    user_ids = [user_id[0] for user_id in user_ids_with_orders]
    
    # Then get the user objects
    staff_users = User.query.filter(User.id.in_(user_ids)).all()
    
    # If no users found with orders, fallback to users with Cashier role
    cashier_role = Role.query.filter_by(name='Cashier').first()
    if not staff_users and cashier_role:
        staff_users = User.query.join(UserRole).join(Role).filter(
            Role.name == 'Cashier'
        ).all()
    
    # Prepare report data based on report type
    if report_type == 'sales':
        report_data = generate_sales_report(staff_users, start_date, end_date)
        report_title = 'Sales Performance Report'
    elif report_type == 'attendance':
        report_data = generate_attendance_report(staff_users, start_date, end_date)
        report_title = 'Attendance Report'
    elif report_type == 'productivity':
        report_data = generate_productivity_report(staff_users, start_date, end_date)
        report_title = 'Productivity Report'
    else:
        report_data = generate_sales_report(staff_users, start_date, end_date)
        report_title = 'Sales Performance Report'
    
    return render_template('manager/employee_reports.html',
                          date_range=date_range,
                          report_type=report_type,
                          start_date=start_date.strftime('%Y-%m-%d'),
                          end_date=end_date.strftime('%Y-%m-%d'),
                          date_label=date_label,
                          report_title=report_title,
                          report_data=report_data,
                          employees=staff_users)

def generate_sales_report(employees, start_date, end_date):
    """Generate sales performance report for employees"""
    report_data = {
        'summary': {
            'total_sales': 0,
            'total_orders': 0,
            'total_items': 0,
            'avg_order_value': 0
        },
        'employee_data': [],
        'daily_sales': {},
        'top_products': []
    }
    
    # Calculate overall sales metrics
    total_sales_query = db.session.query(func.sum(POSOrder.total_amount)).filter(
        func.date(POSOrder.order_date) >= start_date,
        func.date(POSOrder.order_date) <= end_date,
        POSOrder.state == 'paid'
    ).scalar()
    
    total_orders_query = POSOrder.query.filter(
        func.date(POSOrder.order_date) >= start_date,
        func.date(POSOrder.order_date) <= end_date,
        POSOrder.state == 'paid'
    ).count()
    
    total_items_query = db.session.query(func.sum(POSOrderLine.quantity)).join(
        POSOrder, POSOrder.id == POSOrderLine.order_id
    ).filter(
        func.date(POSOrder.order_date) >= start_date,
        func.date(POSOrder.order_date) <= end_date,
        POSOrder.state == 'paid'
    ).scalar()
    
    report_data['summary']['total_sales'] = total_sales_query or 0
    report_data['summary']['total_orders'] = total_orders_query or 0
    report_data['summary']['total_items'] = total_items_query or 0
    
    if total_orders_query and total_orders_query > 0:
        report_data['summary']['avg_order_value'] = (total_sales_query or 0) / total_orders_query
    
    # Calculate per-employee metrics
    for employee in employees:
        # Get employee sales data
        employee_sales = db.session.query(func.sum(POSOrder.total_amount)).filter(
            func.date(POSOrder.order_date) >= start_date,
            func.date(POSOrder.order_date) <= end_date,
            POSOrder.state == 'paid',
            POSOrder.created_by == employee.id
        ).scalar() or 0
        
        employee_orders = POSOrder.query.filter(
            func.date(POSOrder.order_date) >= start_date,
            func.date(POSOrder.order_date) <= end_date,
            POSOrder.state == 'paid',
            POSOrder.created_by == employee.id
        ).count()
        
        employee_items = db.session.query(func.sum(POSOrderLine.quantity)).join(
            POSOrder, POSOrder.id == POSOrderLine.order_id
        ).filter(
            func.date(POSOrder.order_date) >= start_date,
            func.date(POSOrder.order_date) <= end_date,
            POSOrder.state == 'paid',
            POSOrder.created_by == employee.id
        ).scalar() or 0
        
        # Calculate average order value
        avg_order = employee_sales / employee_orders if employee_orders > 0 else 0
        
        # Calculate sales percentage of total
        sales_percentage = (employee_sales / report_data['summary']['total_sales'] * 100) if report_data['summary']['total_sales'] > 0 else 0
        
        # Add employee data to report
        report_data['employee_data'].append({
            'id': employee.id,
            'name': f"{employee.first_name or ''} {employee.last_name or ''}".strip() or employee.username,
            'username': employee.username,
            'sales': employee_sales,
            'orders': employee_orders,
            'items': employee_items,
            'avg_order': avg_order,
            'sales_percentage': sales_percentage
        })
    
    # Sort employee data by sales (highest first)
    report_data['employee_data'].sort(key=lambda x: x['sales'], reverse=True)
    
    # Calculate daily sales for the date range
    current_date = start_date
    dates = []
    daily_sales = []
    
    while current_date <= end_date:
        dates.append(current_date.strftime('%Y-%m-%d'))
        
        # Get sales for this day
        day_sales = db.session.query(func.sum(POSOrder.total_amount)).filter(
            func.date(POSOrder.order_date) == current_date,
            POSOrder.state == 'paid'
        ).scalar() or 0
        
        daily_sales.append(day_sales)
        
        # Store employee-specific sales for this day
        employee_sales_for_day = {}
        for employee in employees:
            emp_sales = db.session.query(func.sum(POSOrder.total_amount)).filter(
                func.date(POSOrder.order_date) == current_date,
                POSOrder.state == 'paid',
                POSOrder.created_by == employee.id
            ).scalar() or 0
            
            employee_sales_for_day[employee.id] = emp_sales
        
        report_data['daily_sales'][current_date.strftime('%Y-%m-%d')] = {
            'total': day_sales,
            'employee_sales': employee_sales_for_day
        }
        
        current_date += timedelta(days=1)
    
    # Get top selling products for the period
    top_products_query = db.session.query(
        Product.id,
        Product.name,
        func.sum(POSOrderLine.quantity).label('quantity'),
        func.sum(POSOrderLine.price_subtotal).label('sales')
    ).join(
        POSOrderLine, POSOrderLine.product_id == Product.id
    ).join(
        POSOrder, POSOrder.id == POSOrderLine.order_id
    ).filter(
        func.date(POSOrder.order_date) >= start_date,
        func.date(POSOrder.order_date) <= end_date,
        POSOrder.state == 'paid'
    ).group_by(
        Product.id
    ).order_by(
        func.sum(POSOrderLine.quantity).desc()
    ).limit(10).all()
    
    for product in top_products_query:
        report_data['top_products'].append({
            'id': product.id,
            'name': product.name,
            'quantity': product.quantity,
            'sales': product.sales
        })
    
    # Add chart data
    report_data['chart_data'] = {
        'dates': dates,
        'daily_sales': daily_sales,
        'employee_names': [emp['name'] for emp in report_data['employee_data']],
        'employee_sales': [emp['sales'] for emp in report_data['employee_data']]
    }
    
    return report_data

def generate_attendance_report(employees, start_date, end_date):
    """Generate attendance report for employees"""
    report_data = {
        'summary': {
            'total_sessions': 0,
            'avg_session_duration': 0
        },
        'employee_data': [],
        'daily_sessions': {}
    }
    
    # Calculate overall attendance metrics
    total_sessions_query = POSSession.query.filter(
        func.date(POSSession.start_time) >= start_date,
        func.date(POSSession.start_time) <= end_date
    ).count()
    
    report_data['summary']['total_sessions'] = total_sessions_query or 0
    
    # Calculate session durations
    all_sessions = POSSession.query.filter(
        func.date(POSSession.start_time) >= start_date,
        func.date(POSSession.start_time) <= end_date,
        POSSession.end_time != None
    ).all()
    
    total_duration = 0
    for session in all_sessions:
        if session.end_time:
            duration = (session.end_time - session.start_time).total_seconds() / 3600  # hours
            total_duration += duration
    
    if all_sessions:
        report_data['summary']['avg_session_duration'] = total_duration / len(all_sessions)
    
    # Calculate per-employee metrics
    for employee in employees:
        # Get employee session data
        employee_sessions = POSSession.query.filter(
            func.date(POSSession.start_time) >= start_date,
            func.date(POSSession.start_time) <= end_date,
            POSSession.user_id == employee.id
        ).all()
        
        session_count = len(employee_sessions)
        
        # Calculate total hours worked
        total_hours = 0
        completed_sessions = 0
        
        for session in employee_sessions:
            if session.end_time:
                duration = (session.end_time - session.start_time).total_seconds() / 3600  # hours
                total_hours += duration
                completed_sessions += 1
        
        # Calculate average session duration
        avg_session_duration = total_hours / completed_sessions if completed_sessions > 0 else 0
        
        # Calculate attendance percentage
        days_in_period = (end_date - start_date).days + 1
        attendance_percentage = (session_count / days_in_period * 100) if days_in_period > 0 else 0
        
        # Add employee data to report
        report_data['employee_data'].append({
            'id': employee.id,
            'name': f"{employee.first_name or ''} {employee.last_name or ''}".strip() or employee.username,
            'username': employee.username,
            'sessions': session_count,
            'hours_worked': total_hours,
            'avg_session_duration': avg_session_duration,
            'attendance_percentage': min(attendance_percentage, 100)  # Cap at 100%
        })
    
    # Sort employee data by hours worked (highest first)
    report_data['employee_data'].sort(key=lambda x: x['hours_worked'], reverse=True)
    
    # Calculate daily sessions for the date range
    current_date = start_date
    dates = []
    daily_sessions_count = []
    
    while current_date <= end_date:
        dates.append(current_date.strftime('%Y-%m-%d'))
        
        # Get sessions for this day
        day_sessions = POSSession.query.filter(
            func.date(POSSession.start_time) == current_date
        ).count()
        
        daily_sessions_count.append(day_sessions)
        
        # Store employee-specific sessions for this day
        employee_sessions_for_day = {}
        for employee in employees:
            emp_sessions = POSSession.query.filter(
                func.date(POSSession.start_time) == current_date,
                POSSession.user_id == employee.id
            ).count()
            
            employee_sessions_for_day[employee.id] = emp_sessions
        
        report_data['daily_sessions'][current_date.strftime('%Y-%m-%d')] = {
            'total': day_sessions,
            'employee_sessions': employee_sessions_for_day
        }
        
        current_date += timedelta(days=1)
    
    # Add chart data
    report_data['chart_data'] = {
        'dates': dates,
        'daily_sessions': daily_sessions_count,
        'employee_names': [emp['name'] for emp in report_data['employee_data']],
        'employee_hours': [emp['hours_worked'] for emp in report_data['employee_data']]
    }
    
    return report_data

def generate_productivity_report(employees, start_date, end_date):
    """Generate productivity report for employees"""
    report_data = {
        'summary': {
            'avg_sales_per_hour': 0,
            'avg_orders_per_hour': 0
        },
        'employee_data': []
    }
    
    # Calculate overall productivity metrics
    total_sales_query = db.session.query(func.sum(POSOrder.total_amount)).filter(
        func.date(POSOrder.order_date) >= start_date,
        func.date(POSOrder.order_date) <= end_date,
        POSOrder.state == 'paid'
    ).scalar() or 0
    
    total_orders_query = POSOrder.query.filter(
        func.date(POSOrder.order_date) >= start_date,
        func.date(POSOrder.order_date) <= end_date,
        POSOrder.state == 'paid'
    ).count()
    
    # Calculate total hours worked across all employees
    all_sessions = POSSession.query.filter(
        func.date(POSSession.start_time) >= start_date,
        func.date(POSSession.start_time) <= end_date,
        POSSession.end_time != None
    ).all()
    
    total_hours = 0
    for session in all_sessions:
        if session.end_time:
            duration = (session.end_time - session.start_time).total_seconds() / 3600  # hours
            total_hours += duration
    
    # Calculate productivity metrics
    if total_hours > 0:
        report_data['summary']['avg_sales_per_hour'] = total_sales_query / total_hours
        report_data['summary']['avg_orders_per_hour'] = total_orders_query / total_hours
    
    # Calculate per-employee metrics
    for employee in employees:
        # Get employee sales data
        employee_sales = db.session.query(func.sum(POSOrder.total_amount)).filter(
            func.date(POSOrder.order_date) >= start_date,
            func.date(POSOrder.order_date) <= end_date,
            POSOrder.state == 'paid',
            POSOrder.created_by == employee.id
        ).scalar() or 0
        
        employee_orders = POSOrder.query.filter(
            func.date(POSOrder.order_date) >= start_date,
            func.date(POSOrder.order_date) <= end_date,
            POSOrder.state == 'paid',
            POSOrder.created_by == employee.id
        ).count()
        
        # Get employee session data to calculate hours worked
        employee_sessions = POSSession.query.filter(
            func.date(POSSession.start_time) >= start_date,
            func.date(POSSession.start_time) <= end_date,
            POSSession.user_id == employee.id,
            POSSession.end_time != None
        ).all()
        
        employee_hours = 0
        for session in employee_sessions:
            if session.end_time:
                duration = (session.end_time - session.start_time).total_seconds() / 3600  # hours
                employee_hours += duration
        
        # Calculate productivity metrics
        sales_per_hour = employee_sales / employee_hours if employee_hours > 0 else 0
        orders_per_hour = employee_orders / employee_hours if employee_hours > 0 else 0
        
        # Calculate efficiency compared to average
        sales_efficiency = (sales_per_hour / report_data['summary']['avg_sales_per_hour'] * 100) if report_data['summary']['avg_sales_per_hour'] > 0 else 0
        orders_efficiency = (orders_per_hour / report_data['summary']['avg_orders_per_hour'] * 100) if report_data['summary']['avg_orders_per_hour'] > 0 else 0
        
        # Add employee data to report
        report_data['employee_data'].append({
            'id': employee.id,
            'name': f"{employee.first_name or ''} {employee.last_name or ''}".strip() or employee.username,
            'username': employee.username,
            'sales': employee_sales,
            'orders': employee_orders,
            'hours_worked': employee_hours,
            'sales_per_hour': sales_per_hour,
            'orders_per_hour': orders_per_hour,
            'sales_efficiency': sales_efficiency,
            'orders_efficiency': orders_efficiency
        })
    
    # Sort employee data by sales per hour (highest first)
    report_data['employee_data'].sort(key=lambda x: x['sales_per_hour'], reverse=True)
    
    # Add chart data
    report_data['chart_data'] = {
        'employee_names': [emp['name'] for emp in report_data['employee_data']],
        'sales_per_hour': [emp['sales_per_hour'] for emp in report_data['employee_data']],
        'orders_per_hour': [emp['orders_per_hour'] for emp in report_data['employee_data']]
    }
    
    return report_data

# Export employee report as CSV
@manager_bp.route('/export-employee-report')
@login_required
@manager_required
def export_employee_report():
    # Get filter parameters
    date_range = request.args.get('date_range', 'this_month')
    report_type = request.args.get('report_type', 'sales')
    
    # Calculate date range
    today = datetime.now().date()
    
    if date_range == 'today':
        start_date = today
        end_date = today
    elif date_range == 'yesterday':
        start_date = today - timedelta(days=1)
        end_date = today - timedelta(days=1)
    elif date_range == 'this_week':
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif date_range == 'last_week':
        start_date = today - timedelta(days=today.weekday() + 7)
        end_date = today - timedelta(days=today.weekday() + 1)
    elif date_range == 'this_month':
        start_date = date(today.year, today.month, 1)
        end_date = today
    elif date_range == 'last_month':
        if today.month == 1:
            start_date = date(today.year - 1, 12, 1)
            end_date = date(today.year, 1, 1) - timedelta(days=1)
        else:
            start_date = date(today.year, today.month - 1, 1)
            end_date = date(today.year, today.month, 1) - timedelta(days=1)
    elif date_range == 'custom':
        try:
            start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            start_date = date(today.year, today.month, 1)
            end_date = today
    else:
        start_date = date(today.year, today.month, 1)
        end_date = today
    
    # Get all users who have created POS orders
    user_ids_with_orders = db.session.query(POSOrder.created_by).distinct().filter(
        POSOrder.created_by.isnot(None),
        func.date(POSOrder.order_date) >= start_date,
        func.date(POSOrder.order_date) <= end_date,
        POSOrder.state == 'paid'
    ).all()
    
    user_ids = [user_id[0] for user_id in user_ids_with_orders]
    
    # Then get the user objects
    staff_users = User.query.filter(User.id.in_(user_ids)).all()
    
    # If no users found with orders, fallback to users with Cashier role
    cashier_role = Role.query.filter_by(name='Cashier').first()
    if not staff_users and cashier_role:
        staff_users = User.query.join(UserRole).join(Role).filter(
            Role.name == 'Cashier'
        ).all()
    
    # Prepare report data based on report type
    if report_type == 'sales':
        report_data = generate_sales_report(staff_users, start_date, end_date)
        filename = f"sales_report_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
        headers = ['Employee', 'Sales (₵)', 'Orders', 'Items Sold', 'Avg Order Value (₵)', 'Sales %']
        
        # Create CSV data
        csv_data = []
        csv_data.append(headers)
        
        for emp in report_data['employee_data']:
            csv_data.append([
                emp['name'],
                f"{emp['sales']:.2f}",
                str(emp['orders']),
                str(emp['items']),
                f"{emp['avg_order']:.2f}",
                f"{emp['sales_percentage']:.2f}%"
            ])
        
        # Add summary row
        csv_data.append([])
        csv_data.append([
            'TOTAL',
            f"{report_data['summary']['total_sales']:.2f}",
            str(report_data['summary']['total_orders']),
            str(report_data['summary']['total_items']),
            f"{report_data['summary']['avg_order_value']:.2f}",
            '100.00%'
        ])
        
    elif report_type == 'attendance':
        report_data = generate_attendance_report(staff_users, start_date, end_date)
        filename = f"attendance_report_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
        headers = ['Employee', 'Sessions', 'Hours Worked', 'Avg Session Duration (hrs)', 'Attendance %']
        
        # Create CSV data
        csv_data = []
        csv_data.append(headers)
        
        for emp in report_data['employee_data']:
            csv_data.append([
                emp['name'],
                str(emp['sessions']),
                f"{emp['hours_worked']:.2f}",
                f"{emp['avg_session_duration']:.2f}",
                f"{emp['attendance_percentage']:.2f}%"
            ])
        
        # Add summary row
        csv_data.append([])
        csv_data.append([
            'AVERAGE',
            f"{report_data['summary']['total_sessions'] / len(staff_users) if staff_users else 0:.2f}",
            '',
            f"{report_data['summary']['avg_session_duration']:.2f}",
            ''
        ])
        
    elif report_type == 'productivity':
        report_data = generate_productivity_report(staff_users, start_date, end_date)
        filename = f"productivity_report_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
        headers = ['Employee', 'Sales (₵)', 'Orders', 'Hours Worked', 'Sales/Hour (₵)', 'Orders/Hour', 'Sales Efficiency %', 'Orders Efficiency %']
        
        # Create CSV data
        csv_data = []
        csv_data.append(headers)
        
        for emp in report_data['employee_data']:
            csv_data.append([
                emp['name'],
                f"{emp['sales']:.2f}",
                str(emp['orders']),
                f"{emp['hours_worked']:.2f}",
                f"{emp['sales_per_hour']:.2f}",
                f"{emp['orders_per_hour']:.2f}",
                f"{emp['sales_efficiency']:.2f}%",
                f"{emp['orders_efficiency']:.2f}%"
            ])
        
        # Add summary row
        csv_data.append([])
        csv_data.append([
            'AVERAGE',
            '',
            '',
            '',
            f"{report_data['summary']['avg_sales_per_hour']:.2f}",
            f"{report_data['summary']['avg_orders_per_hour']:.2f}",
            '100.00%',
            '100.00%'
        ])
    
    else:
        # Default to sales report
        report_data = generate_sales_report(staff_users, start_date, end_date)
        filename = f"sales_report_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
        headers = ['Employee', 'Sales (₵)', 'Orders', 'Items Sold', 'Avg Order Value (₵)', 'Sales %']
        
        # Create CSV data
        csv_data = []
        csv_data.append(headers)
        
        for emp in report_data['employee_data']:
            csv_data.append([
                emp['name'],
                f"{emp['sales']:.2f}",
                str(emp['orders']),
                str(emp['items']),
                f"{emp['avg_order']:.2f}",
                f"{emp['sales_percentage']:.2f}%"
            ])
        
        # Add summary row
        csv_data.append([])
        csv_data.append([
            'TOTAL',
            f"{report_data['summary']['total_sales']:.2f}",
            str(report_data['summary']['total_orders']),
            str(report_data['summary']['total_items']),
            f"{report_data['summary']['avg_order_value']:.2f}",
            '100.00%'
        ])
    
    # Create CSV response
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    for row in csv_data:
        writer.writerow(row)
    
    response = jsonify({
        'csv': output.getvalue(),
        'filename': filename
    })
    
    return response

# Sales Worker Monitoring Dashboard
@manager_bp.route('/sales-worker-dashboard')
@login_required
@manager_required
def sales_worker_dashboard():
    # Get filter parameters
    date_range = request.args.get('date_range', 'this_month')
    
    # Calculate date range
    today = datetime.now().date()
    
    if date_range == 'today':
        start_date = today
        end_date = today
    elif date_range == 'yesterday':
        start_date = today - timedelta(days=1)
        end_date = today - timedelta(days=1)
    elif date_range == 'this_week':
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif date_range == 'last_week':
        start_date = today - timedelta(days=today.weekday() + 7)
        end_date = today - timedelta(days=today.weekday() + 1)
    elif date_range == 'this_month':
        start_date = date(today.year, today.month, 1)
        end_date = today
    elif date_range == 'last_month':
        if today.month == 1:
            start_date = date(today.year - 1, 12, 1)
            end_date = date(today.year, 1, 1) - timedelta(days=1)
        else:
            start_date = date(today.year, today.month - 1, 1)
            end_date = date(today.year, today.month, 1) - timedelta(days=1)
    elif date_range == 'custom':
        try:
            start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            start_date = date(today.year, today.month, 1)
            end_date = today
    else:
        start_date = date(today.year, today.month, 1)
        end_date = today
    
    # Get all users who have created POS orders
    user_ids = db.session.query(POSOrder.created_by).distinct().all()
    user_ids = [user_id[0] for user_id in user_ids if user_id[0] is not None]
    staff_users = User.query.filter(User.id.in_(user_ids)).all()
    
    staff_performance = []
    staff_names = []
    gross_sales_data = []
    returns_data = []
    net_sales_data = []
    
    for user in staff_users:
        # Calculate gross sales amount
        gross_sales = db.session.query(func.sum(POSOrder.total_amount)).filter(
            func.date(POSOrder.order_date) >= start_date,
            func.date(POSOrder.order_date) <= end_date,
            POSOrder.state == 'paid',
            POSOrder.created_by == user.id
        ).scalar() or 0
        
        # Calculate returns amount
        returns_amount = db.session.query(func.sum(POSReturn.refund_amount)).filter(
            func.date(POSReturn.return_date) >= start_date,
            func.date(POSReturn.return_date) <= end_date,
            POSReturn.state == 'validated',
            POSReturn.created_by == user.id
        ).scalar() or 0
        
        # Calculate net sales (sales minus returns)
        net_sales = max(0, gross_sales - returns_amount)
        
        # Calculate order count
        order_count = POSOrder.query.filter(
            func.date(POSOrder.order_date) >= start_date,
            func.date(POSOrder.order_date) <= end_date,
            POSOrder.state == 'paid',
            POSOrder.created_by == user.id
        ).count()
        
        # Calculate items sold
        items_sold = db.session.query(func.sum(POSOrderLine.quantity)).join(
            POSOrder, POSOrder.id == POSOrderLine.order_id
        ).filter(
            func.date(POSOrder.order_date) >= start_date,
            func.date(POSOrder.order_date) <= end_date,
            POSOrder.state == 'paid',
            POSOrder.created_by == user.id
        ).scalar() or 0
        
        # Calculate return rate
        return_rate = (returns_amount / gross_sales * 100) if gross_sales > 0 else 0
        
        # Calculate average order value
        average_order = (net_sales / order_count) if order_count > 0 else 0
        
        staff_performance.append({
            'id': user.id,
            'username': user.username,
            'gross_sales': gross_sales,
            'returns_amount': returns_amount,
            'net_sales': net_sales,
            'order_count': order_count,
            'items_sold': items_sold,
            'return_rate': return_rate,
            'average_order': average_order
        })
        
        staff_names.append(user.username)
        gross_sales_data.append(gross_sales)
        returns_data.append(returns_amount)
        net_sales_data.append(net_sales)
    
    # Sort staff performance by net sales
    staff_performance.sort(key=lambda x: x['net_sales'], reverse=True)
    
    # Calculate totals
    total_workers = len(staff_performance)
    total_gross_sales = sum(staff['gross_sales'] for staff in staff_performance)
    total_returns = sum(staff['returns_amount'] for staff in staff_performance)
    total_net_sales = sum(staff['net_sales'] for staff in staff_performance)
    
    # Get top performers
    top_net_sales_staff = sorted(staff_performance, key=lambda x: x['net_sales'], reverse=True)[:5]
    
    # Get staff with lowest return rates (who have at least some sales)
    active_staff = [s for s in staff_performance if s['gross_sales'] > 0]
    lowest_return_rate_staff = sorted(active_staff, key=lambda x: x['return_rate'])[:5]
    
    # Generate performance targets
    staff_targets = []
    for staff in staff_performance:
        # Set targets based on performance
        sales_target = staff['net_sales'] * 1.2  # 20% higher than current
        orders_target = staff['order_count'] * 1.2  # 20% higher than current
        
        # For return rate, target should be lower than current (if current is already low, set a minimum)
        return_rate_target = min(staff['return_rate'], 5) if staff['return_rate'] > 2 else 2
        
        staff_targets.append({
            'username': staff['username'],
            'net_sales': staff['net_sales'],
            'sales_target': sales_target,
            'order_count': staff['order_count'],
            'orders_target': int(orders_target),
            'return_rate': staff['return_rate'],
            'return_rate_target': return_rate_target
        })
    
    return render_template('manager/sales_worker_dashboard.html',
                          date_range=date_range,
                          start_date=start_date.strftime('%Y-%m-%d'),
                          end_date=end_date.strftime('%Y-%m-%d'),
                          staff_performance=staff_performance,
                          staff_names=staff_names,
                          gross_sales_data=gross_sales_data,
                          returns_data=returns_data,
                          net_sales_data=net_sales_data,
                          total_workers=total_workers,
                          total_gross_sales=total_gross_sales,
                          total_returns=total_returns,
                          total_net_sales=total_net_sales,
                          top_net_sales_staff=top_net_sales_staff,
                          lowest_return_rate_staff=lowest_return_rate_staff,
                          staff_targets=staff_targets)
