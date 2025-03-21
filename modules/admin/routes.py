from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from modules.auth.models import User, Role
from modules.pos.models import POSSession, POSOrder, POSReturn
from modules.inventory.models import Product, StockMove
from sqlalchemy import func
from datetime import datetime, date
from werkzeug.security import generate_password_hash

admin = Blueprint('admin', __name__, url_prefix='/admin')

@admin.route('/')
@login_required
def dashboard():
    """Admin dashboard with comprehensive system overview"""
    # Check if user has admin role
    if not current_user.has_role('Admin'):
        flash('You do not have permission to access the admin dashboard.', 'danger')
        return redirect(url_for('pos.index'))
    
    # Get statistics for the dashboard
    today = datetime.utcnow().date()
    
    # Today's orders and sales (all users)
    today_orders = POSOrder.query.filter(
        func.date(POSOrder.order_date) == today
    ).count()
    
    today_sales_query = db.session.query(func.sum(POSOrder.total_amount)).filter(
        func.date(POSOrder.order_date) == today
    ).scalar()
    today_sales = today_sales_query if today_sales_query else 0
    
    # Get active sessions
    active_sessions = POSSession.query.filter_by(state='open').count()
    
    # Get all users
    users = User.query.all()
    
    # Get recent orders (last 10)
    recent_orders = POSOrder.query.order_by(POSOrder.order_date.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                          today_orders=today_orders,
                          today_sales=today_sales,
                          active_sessions=active_sessions,
                          users=users,
                          recent_orders=recent_orders)

@admin.route('/users/new', methods=['GET', 'POST'])
@login_required
def create_user():
    """Create a new user"""
    # Check if user has admin role
    if not current_user.has_role('Admin'):
        flash('You do not have permission to create users.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role_id = request.form.get('role')
        
        # Validate input
        if not username or not email or not password or not role_id:
            flash('All fields are required.', 'danger')
            return redirect(url_for('admin.create_user'))
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('admin.create_user'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return redirect(url_for('admin.create_user'))
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        # Add role
        role = Role.query.get(role_id)
        if role:
            new_user.roles.append(role)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('User created successfully.', 'success')
        return redirect(url_for('admin.dashboard'))
    
    # Get all roles for the form
    roles = Role.query.all()
    return render_template('admin/user_form.html', roles=roles, user=None)

@admin.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """Edit an existing user"""
    # Check if user has admin role
    if not current_user.has_role('Admin'):
        flash('You do not have permission to edit users.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role_id = request.form.get('role')
        is_active = 'is_active' in request.form
        
        # Validate input
        if not username or not email or not role_id:
            flash('Username, email, and role are required.', 'danger')
            return redirect(url_for('admin.edit_user', user_id=user_id))
        
        # Check if username already exists (excluding current user)
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != user_id:
            flash('Username already exists.', 'danger')
            return redirect(url_for('admin.edit_user', user_id=user_id))
        
        # Check if email already exists (excluding current user)
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != user_id:
            flash('Email already exists.', 'danger')
            return redirect(url_for('admin.edit_user', user_id=user_id))
        
        # Update user
        user.username = username
        user.email = email
        user.is_active = is_active
        
        # Update password if provided
        if password:
            user.password_hash = generate_password_hash(password)
        
        # Update role
        role = Role.query.get(role_id)
        if role:
            user.roles = [role]  # Replace existing roles
        
        db.session.commit()
        
        flash('User updated successfully.', 'success')
        return redirect(url_for('admin.dashboard'))
    
    # Get all roles for the form
    roles = Role.query.all()
    return render_template('admin/user_form.html', roles=roles, user=user)

@admin.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    """Delete a user"""
    # Check if user has admin role
    if not current_user.has_role('Admin'):
        flash('You do not have permission to delete users.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting yourself
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin.dashboard'))

@admin.route('/sales-overview')
@login_required
def sales_overview():
    """Comprehensive sales overview for all users"""
    # Check if user has admin role
    if not current_user.has_role('Admin'):
        flash('You do not have permission to access sales overview.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    # Get filter parameters
    selected_date = request.args.get('date', date.today().isoformat())
    
    # Convert string date to date object
    try:
        filter_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except ValueError:
        filter_date = date.today()
    
    # Get all orders for the selected date
    orders = POSOrder.query.filter(
        func.date(POSOrder.order_date) == filter_date
    ).all()
    
    # Calculate sales by user
    sales_by_user = {}
    for order in orders:
        user = User.query.get(order.created_by)
        username = user.username if user else "Unknown"
        
        if username not in sales_by_user:
            sales_by_user[username] = {
                'order_count': 0,
                'total_sales': 0,
                'orders': []
            }
        
        sales_by_user[username]['order_count'] += 1
        sales_by_user[username]['total_sales'] += order.total_amount
        sales_by_user[username]['orders'].append(order)
    
    # Calculate overall totals
    total_orders = len(orders)
    total_sales = sum(order.total_amount for order in orders)
    
    return render_template('admin/sales_overview.html',
                          filter_date=filter_date,
                          sales_by_user=sales_by_user,
                          total_orders=total_orders,
                          total_sales=total_sales)

@admin.route('/inventory-overview')
@login_required
def inventory_overview():
    """Comprehensive inventory overview"""
    # Check if user has admin role
    if not current_user.has_role('Admin'):
        flash('You do not have permission to access inventory overview.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    # Get all products with low stock (less than 10 units)
    low_stock_products = Product.query.filter(Product.quantity < 10).all()
    
    # Get recent stock movements
    recent_movements = StockMove.query.order_by(StockMove.date.desc()).limit(20).all()
    
    return render_template('admin/inventory_overview.html',
                          low_stock_products=low_stock_products,
                          recent_movements=recent_movements)

@admin.route('/user-activity/<int:user_id>')
@login_required
def user_activity(user_id):
    """View detailed activity for a specific user"""
    # Check if user has admin role
    if not current_user.has_role('Admin'):
        flash('You do not have permission to view user activity.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # Get user's orders
    orders = POSOrder.query.filter_by(created_by=user_id).order_by(POSOrder.order_date.desc()).all()
    
    # Get user's sessions
    sessions = POSSession.query.filter_by(user_id=user_id).order_by(POSSession.start_time.desc()).all()
    
    return render_template('admin/user_activity.html', 
                          user=user,
                          orders=orders,
                          sessions=sessions)

@admin.route('/system-reset', methods=['GET', 'POST'])
@login_required
def system_reset():
    """Special page for hard resetting the entire system database"""
    # Check if user has admin role
    if not current_user.has_role('Admin'):
        flash('You do not have permission to access system reset.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    # Track if reset was successful
    reset_success = False
    
    if request.method == 'POST' and 'confirm_reset' in request.form:
        try:
            # Delete all data from all tables in a specific order to avoid foreign key constraints
            
            # Get all table names from the database using reflection
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            # Disable foreign key checks temporarily
            db.session.execute(text("PRAGMA foreign_keys = OFF"))
            
            # First delete all data from specific tables that might have foreign key relationships
            # POS related tables
            if 'pos_order_lines' in tables:
                db.session.execute(text("DELETE FROM pos_order_lines"))
            if 'pos_order_payments' in tables:
                db.session.execute(text("DELETE FROM pos_order_payments"))
            if 'pos_returns' in tables:
                db.session.execute(text("DELETE FROM pos_returns"))
            if 'pos_orders' in tables:
                db.session.execute(text("DELETE FROM pos_orders"))
            if 'pos_sessions' in tables:
                db.session.execute(text("DELETE FROM pos_sessions"))
            if 'pos_payment_methods' in tables:
                db.session.execute(text("DELETE FROM pos_payment_methods"))
            
            # Inventory related tables
            if 'stock_moves' in tables:
                db.session.execute(text("DELETE FROM stock_moves"))
            if 'inventory_lines' in tables:
                db.session.execute(text("DELETE FROM inventory_lines"))
            if 'inventories' in tables:
                db.session.execute(text("DELETE FROM inventories"))
            if 'products' in tables:
                db.session.execute(text("DELETE FROM products"))
            
            # Sales related tables
            if 'sales_orders' in tables:
                db.session.execute(text("DELETE FROM sales_orders"))
            if 'sales_order_lines' in tables:
                db.session.execute(text("DELETE FROM sales_order_lines"))
            if 'invoices' in tables:
                db.session.execute(text("DELETE FROM invoices"))
            if 'invoice_lines' in tables:
                db.session.execute(text("DELETE FROM invoice_lines"))
            
            # Re-enable foreign key checks
            db.session.execute(text("PRAGMA foreign_keys = ON"))
            
            # Commit the changes
            db.session.commit()
            
            flash('System has been completely reset. All data has been cleared.', 'success')
            reset_success = True
        except Exception as e:
            db.session.rollback()
            flash(f'Error during system reset: {str(e)}', 'danger')
    
    return render_template('admin/system_reset.html', reset_success=reset_success)
