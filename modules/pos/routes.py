from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from datetime import datetime, date
from sqlalchemy import func, desc
from modules.inventory.models import Product, StockMove, StockLocation
from modules.sales.models import Customer
from extensions import db
from modules.pos.models import POSSession, POSCashRegister, POSOrder, POSOrderLine, POSCategory, POSPaymentMethod, POSDiscount, POSTax, POSReceiptSettings, POSSettings, POSReturn, POSReturnLine, QualityCheck
from modules.pos.forms import POSSessionForm, POSCashRegisterForm, POSCategoryForm, POSPaymentMethodForm, POSDiscountForm, POSTaxForm, POSReceiptSettingsForm, POSSettingsForm
from modules.inventory.models import Product, StockMove, StockLocation, Category
from modules.sales.models import Customer, SalesOrder, SalesOrderLine
from modules.auth.models import User
from datetime import datetime, date, timedelta
from werkzeug.utils import secure_filename
import os
import tempfile
from collections import defaultdict
from sqlalchemy import text, func, desc
import json

pos = Blueprint('pos', __name__, url_prefix='/pos')

# POS Dashboard
@pos.route('/')
@login_required
def index():
    active_session = POSSession.query.filter_by(user_id=current_user.id, state='open').first()
    
    # Get statistics for the dashboard
    from datetime import datetime, timedelta
    today = datetime.utcnow().date()
    
    # Today's orders and sales - filter by current user if they're a sales worker
    orders_query = POSOrder.query.filter(
        func.date(POSOrder.order_date) == today
    )
    
    # If user is a sales worker (not admin or manager), only show their orders
    is_sales_worker = not current_user.has_role('Admin') and not current_user.has_role('Manager')
    if is_sales_worker:
        orders_query = orders_query.filter(POSOrder.created_by == current_user.id)
    
    today_orders = orders_query.count()
    
    # Calculate today's sales with the same user filtering
    sales_query = db.session.query(func.sum(POSOrder.total_amount)).filter(
        func.date(POSOrder.order_date) == today
    )
    
    # Apply the same user filtering for sales
    if is_sales_worker:
        sales_query = sales_query.filter(POSOrder.created_by == current_user.id)
    
    today_sales_result = sales_query.scalar()
    today_sales = today_sales_result if today_sales_result else 0
    
    # Calculate today's returns with the same user filtering
    returns_query = db.session.query(func.sum(POSReturn.refund_amount)).filter(
        func.date(POSReturn.return_date) == today,
        POSReturn.state == 'validated'
    )
    
    # Apply the same user filtering for returns
    if is_sales_worker:
        returns_query = returns_query.filter(POSReturn.created_by == current_user.id)
    
    today_returns_result = returns_query.scalar()
    today_returns = today_returns_result if today_returns_result else 0
    
    # Calculate net sales (sales minus returns)
    today_net_sales = max(0, today_sales - today_returns)
    
    # Get cash balance for the active session or 0 if no active session
    cash_balance = active_session.cash_register.balance if active_session and active_session.cash_register else 0
    
    # Determine if we should show "My" in the dashboard titles
    is_sales_worker = not current_user.has_role('Admin') and not current_user.has_role('Manager')
    
    return render_template('pos/index.html', 
                          active_session=active_session,
                          today_orders=today_orders,
                          today_sales=today_net_sales,
                          today_returns=today_returns,
                          cash_balance=cash_balance,
                          is_sales_worker=is_sales_worker)

# POS Terminal
@pos.route('/terminal')
@login_required
def terminal():
    # Check if there's an active session for the current user
    active_session = POSSession.query.filter_by(user_id=current_user.id, state='open').first()
    
    if not active_session:
        flash('Please open a POS session first.', 'warning')
        return redirect(url_for('pos.index'))
    
    # Get products, categories, and payment methods for the POS terminal
    products = Product.query.filter_by(is_active=True).all()
    categories = Category.query.all()
    payment_methods = POSPaymentMethod.query.filter_by(is_active=True).all()
    customers = Customer.query.filter_by(is_active=True).all()
    
    return render_template('pos/terminal.html', 
                          session=active_session,
                          products=products,
                          categories=categories,
                          payment_methods=payment_methods,
                          customers=customers)

# Odoo-style POS Terminal
@pos.route('/terminal-odoo')
@login_required
def terminal_odoo():
    # Check if there's an active session for the current user
    active_session = POSSession.query.filter_by(user_id=current_user.id, state='open').first()
    
    if not active_session:
        flash('Please open a POS session first.', 'warning')
        return redirect(url_for('pos.index'))
    
    # Get products, categories, and payment methods for the POS terminal
    products = Product.query.filter_by(is_active=True).all()
    categories = Category.query.all()
    payment_methods = POSPaymentMethod.query.filter_by(is_active=True).all()
    customers = Customer.query.filter_by(is_active=True).all()
    
    # Debug information
    print(f"Products count: {len(products)}")
    print(f"Categories count: {len(categories)}")
    if len(products) > 0:
        print(f"First product: {products[0].name}, Category: {products[0].category.name if products[0].category else 'None'}")
    
    return render_template('pos/terminal_odoo_style.html', 
                          session=active_session,
                          products=products,
                          categories=categories,
                          payment_methods=payment_methods,
                          customers=customers,
                          currency='GH₵')

# Unified POS Terminal
@pos.route('/terminal-unified')
@login_required
def terminal_unified():
    # Check if there's an active session for the current user
    active_session = POSSession.query.filter_by(user_id=current_user.id, state='open').first()
    
    if not active_session:
        flash('No active POS session found. Please open a session first.', 'warning')
        return redirect(url_for('pos.index'))
    
    # Get products with stock information
    products = Product.query.all()
    
    # Get categories
    categories = Category.query.all()
    
    # Get payment methods
    payment_methods = [
        {'code': 'cash', 'name': 'Cash'},
        {'code': 'card', 'name': 'Card'},
        {'code': 'momo', 'name': 'Mobile Money'}
    ]
    
    # Get customers
    customers = Customer.query.filter_by(is_active=True).all()
    
    # Check if this is an exchange from a return
    exchange_return_id = request.args.get('exchange_return_id', type=int)
    exchange_return = None
    
    if exchange_return_id:
        exchange_return = POSReturn.query.get(exchange_return_id)
        
    return render_template('pos/terminal_unified.html',
                          session=active_session,
                          products=products,
                          categories=categories,
                          payment_methods=payment_methods,
                          customers=customers,
                          exchange_return=exchange_return,
                          currency='GH₵')

# POS Login
@pos.route('/login', methods=['GET', 'POST'])
@login_required
def login():
    if request.method == 'POST':
        pin = request.form.get('pin')
        
        # In a real application, you would verify the PIN against a stored value
        # For demo purposes, we'll accept any PIN
        if pin:
            # Check if there's an active session for the current user
            active_session = POSSession.query.filter_by(user_id=current_user.id, state='open').first()
            
            if active_session:
                return redirect(url_for('pos.terminal_odoo'))
            else:
                return redirect(url_for('pos.new_session'))
        else:
            flash('Invalid PIN', 'danger')
    
    return render_template('pos/login.html')

# POS Sessions
@pos.route('/sessions')
@login_required
def sessions():
    # For admin and manager users, show all sessions
    # For regular users, only show their own sessions
    if current_user.has_role('Admin') or current_user.has_role('Manager'):
        sessions = POSSession.query.order_by(POSSession.start_time.desc()).all()
    else:
        sessions = POSSession.query.filter_by(user_id=current_user.id).order_by(POSSession.start_time.desc()).all()
    
    # Calculate summary statistics
    active_sessions = sum(1 for session in sessions if session.state == 'open')
    
    # Calculate total sales for today
    today = date.today()
    
    # For admin and manager, show all orders for today
    # For regular users, only show their session orders
    if current_user.has_role('Admin') or current_user.has_role('Manager'):
        today_orders = POSOrder.query.filter(
            func.date(POSOrder.order_date) == today
        ).all()
    else:
        today_orders = POSOrder.query.filter(
            func.date(POSOrder.order_date) == today,
            POSOrder.session_id.in_([session.id for session in sessions])
        ).all()
    
    total_sales = sum(order.total_amount for order in today_orders)
    total_transactions = len(today_orders)
    
    # Calculate total sales for each session (to be used in the template)
    session_sales = {}
    for session in sessions:
        session_orders = POSOrder.query.filter_by(session_id=session.id).all()
        session_sales[session.id] = sum(order.total_amount for order in session_orders)
    
    return render_template(
        'pos/sessions.html',
        sessions=sessions,
        active_sessions=active_sessions,
        total_sales=total_sales,
        total_transactions=total_transactions,
        session_sales=session_sales
    )

@pos.route('/sessions/new', methods=['GET', 'POST'])
@login_required
def new_session():
    # Check if there's already an active session for the current user
    active_session = POSSession.query.filter_by(user_id=current_user.id, state='open').first()
    
    if active_session:
        flash('You already have an active session.', 'warning')
        return redirect(url_for('pos.sessions'))
    
    form = POSSessionForm()
    form.cash_register_id.choices = [(r.id, r.name) for r in POSCashRegister.query.all()]
    
    if form.validate_on_submit():
        # Generate session name (e.g., POS/2023/001)
        last_session = POSSession.query.order_by(POSSession.id.desc()).first()
        session_number = 1
        if last_session:
            session_number = last_session.id + 1
        
        session_name = f"POS/{datetime.utcnow().strftime('%Y')}/{session_number:03d}"
        
        session = POSSession(
            name=session_name,
            user_id=current_user.id,
            start_time=datetime.utcnow(),
            state='open',
            opening_balance=form.opening_balance.data,
            cash_register_id=form.cash_register_id.data,
            notes=form.notes.data
        )
        
        # Update cash register balance
        cash_register = POSCashRegister.query.get(form.cash_register_id.data)
        cash_register.balance += form.opening_balance.data
        
        db.session.add(session)
        db.session.commit()
        
        flash('POS session opened successfully!', 'success')
        return redirect(url_for('pos.terminal'))
    
    return render_template('pos/session_form.html', form=form, title='Open POS Session')


@pos.route('/sessions/<int:session_id>/close', methods=['GET', 'POST'])
@login_required
def close_session(session_id):
    session = POSSession.query.get_or_404(session_id)
    
    # Check if user has access to this session
    if session.user_id != current_user.id and not current_user.has_role('Admin'):
        flash('You do not have permission to close this session.', 'danger')
        return redirect(url_for('pos.sessions'))
    
    # Check if session is already closed
    if session.state == 'closed':
        flash('This session is already closed.', 'warning')
        return redirect(url_for('pos.sessions'))
    
    # Get all orders for this session
    orders = POSOrder.query.filter_by(session_id=session_id).all()
    
    # Calculate total sales
    cash_sales = sum(order.total_amount for order in orders if order.payment_method == 'cash')
    card_sales = sum(order.total_amount for order in orders if order.payment_method == 'card')
    mobile_sales = sum(order.total_amount for order in orders if order.payment_method == 'momo')
    other_sales = sum(order.total_amount for order in orders if order.payment_method not in ['cash', 'card', 'momo'])
    
    if request.method == 'POST':
        closing_balance = request.form.get('closing_balance', type=float)
        closing_notes = request.form.get('closing_notes', '')
        
        if closing_balance is None:
            flash('Please enter a valid closing balance.', 'danger')
        else:
            # Close the session
            session.state = 'closed'
            session.end_time = datetime.utcnow()
            session.closing_balance = closing_balance
            session.notes = closing_notes if not session.notes else session.notes + "\n" + closing_notes
            
            db.session.commit()
            
            flash('Session closed successfully.', 'success')
            
            # Redirect to the sales report
            return redirect(url_for('pos.session_report', session_id=session.id))
    
    return render_template('pos/close_session.html',
                          session=session,
                          cash_sales=cash_sales,
                          card_sales=card_sales,
                          mobile_sales=mobile_sales,
                          other_sales=other_sales,
                          datetime=datetime,
                          title='Close POS Session')


# Orders page
@pos.route('/orders')
@login_required
def orders():
    # Get filter parameters
    selected_date = request.args.get('date', date.today().isoformat())
    payment_method = request.args.get('payment_method', '')
    status = request.args.get('status', '')
    
    # Convert string date to date object
    try:
        filter_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except ValueError:
        filter_date = date.today()
    
    # Base query - filter by date
    query = POSOrder.query.filter(
        func.date(POSOrder.order_date) == filter_date
    )
    
    # For sales workers, only show their own orders
    # For managers and admins, show all orders
    if not current_user.has_role('Admin') and not current_user.has_role('Manager'):
        query = query.filter(POSOrder.created_by == current_user.id)
    
    # Apply additional filters if provided
    if payment_method:
        query = query.filter(POSOrder.payment_method == payment_method)
    
    if status:
        query = query.filter(POSOrder.state == status)
    
    # Get orders sorted by most recent first
    orders = query.order_by(desc(POSOrder.order_date)).all()
    
    # Calculate summary statistics
    total_sales = sum(order.total_amount for order in orders) if orders else 0
    order_count = len(orders)
    average_order = total_sales / order_count if order_count > 0 else 0
    
    # Calculate total items sold
    items_query = db.session.query(func.sum(POSOrderLine.quantity)).join(
        POSOrder
    ).filter(
        func.date(POSOrder.order_date) == filter_date
    )
    
    # Apply the same user filter to the items query
    if not current_user.has_role('Admin') and not current_user.has_role('Manager'):
        items_query = items_query.filter(POSOrder.created_by == current_user.id)
        
    items_sold = items_query.scalar() or 0
    
    return render_template(
        'pos/orders.html',
        orders=orders,
        selected_date=selected_date,
        payment_method=payment_method,
        status=status,
        total_sales=total_sales,
        order_count=order_count,
        average_order=average_order,
        items_sold=items_sold
    )

@pos.route('/orders/<int:order_id>')
@login_required
def view_order(order_id):
    """View details of a specific POS order"""
    order = POSOrder.query.get_or_404(order_id)
    return render_template('pos/order_details.html', order=order)

# View receipt
@pos.route('/receipt/<int:order_id>')
@login_required
def view_receipt(order_id):
    order = POSOrder.query.get_or_404(order_id)
    return render_template('pos/receipt.html', order=order)

# Generate printable receipt
@pos.route('/receipt/<int:order_id>/print')
@login_required
def print_receipt(order_id):
    order = POSOrder.query.get_or_404(order_id)
    return render_template('pos/receipt.html', order=order, print_mode=True)

# POS Categories
@pos.route('/categories')
@login_required
def categories():
    categories = POSCategory.query.all()
    return render_template('pos/categories.html', categories=categories)

@pos.route('/categories/new', methods=['GET', 'POST'])
@login_required
def new_category():
    form = POSCategoryForm()
    form.parent_id.choices = [(0, 'None')] + [(c.id, c.name) for c in POSCategory.query.all()]
    
    if form.validate_on_submit():
        category = POSCategory(
            name=form.name.data,
            parent_id=form.parent_id.data if form.parent_id.data != 0 else None,
            sequence=form.sequence.data
        )
        
        # Handle image upload
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            # Create a unique filename
            unique_filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
            filepath = os.path.join(Config.UPLOAD_FOLDER, 'pos/categories', unique_filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            form.image.data.save(filepath)
            category.image_path = f'/static/uploads/pos/categories/{unique_filename}'
        
        db.session.add(category)
        db.session.commit()
        
        flash('POS category created successfully!', 'success')
        return redirect(url_for('pos.categories'))
    
    return render_template('pos/category_form.html', form=form, title='New POS Category')

# POS Payment Methods
@pos.route('/payment-methods')
@login_required
def payment_methods():
    payment_methods = POSPaymentMethod.query.all()
    return render_template('pos/payment_methods.html', payment_methods=payment_methods)

@pos.route('/config')
@login_required
def config():
    return render_template('pos/config.html')

@pos.route('/payment-methods/new', methods=['GET', 'POST'])
@login_required
def new_payment_method():
    form = POSPaymentMethodForm()
    
    if form.validate_on_submit():
        payment_method = POSPaymentMethod(
            name=form.name.data,
            code=form.code.data,
            is_cash=form.is_cash.data,
            is_active=form.is_active.data
        )
        
        db.session.add(payment_method)
        db.session.commit()
        
        flash('Payment method created successfully!', 'success')
        return redirect(url_for('pos.payment_methods'))
    
    return render_template('pos/payment_method_form.html', form=form, title='New Payment Method')

# POS Cash Registers
@pos.route('/cash-registers')
@login_required
def cash_registers():
    cash_registers = POSCashRegister.query.all()
    return render_template('pos/cash_registers.html', cash_registers=cash_registers)

@pos.route('/cash-registers/new', methods=['GET', 'POST'])
@login_required
def new_cash_register():
    form = POSCashRegisterForm()
    
    if form.validate_on_submit():
        cash_register = POSCashRegister(
            name=form.name.data,
            balance=form.balance.data
        )
        
        db.session.add(cash_register)
        db.session.commit()
        
        flash('Cash register created successfully!', 'success')
        return redirect(url_for('pos.cash_registers'))
    
    return render_template('pos/cash_register_form.html', form=form, title='New Cash Register')

# POS Discounts
@pos.route('/discounts')
@login_required
def discounts():
    discounts = POSDiscount.query.all()
    return render_template('pos/discounts.html', discounts=discounts)

@pos.route('/discounts/new', methods=['GET', 'POST'])
@login_required
def new_discount():
    form = POSDiscountForm()
    
    if form.validate_on_submit():
        discount = POSDiscount(
            name=form.name.data,
            discount_type=form.discount_type.data,
            value=form.value.data,
            is_active=form.is_active.data
        )
        
        db.session.add(discount)
        db.session.commit()
        
        flash('Discount created successfully!', 'success')
        return redirect(url_for('pos.discounts'))
    
    return render_template('pos/discount_form.html', form=form, title='New Discount')

# POS Taxes
@pos.route('/taxes')
@login_required
def taxes():
    taxes = POSTax.query.all()
    return render_template('pos/taxes.html', taxes=taxes)

@pos.route('/taxes/new', methods=['GET', 'POST'])
@login_required
def new_tax():
    form = POSTaxForm()
    
    if form.validate_on_submit():
        tax = POSTax(
            name=form.name.data,
            rate=form.rate.data,
            is_active=form.is_active.data
        )
        
        db.session.add(tax)
        db.session.commit()
        
        flash('Tax created successfully!', 'success')
        return redirect(url_for('pos.taxes'))
    
    return render_template('pos/tax_form.html', form=form, title='New Tax')

# POS Receipt Customization
@pos.route('/receipt-settings', methods=['GET', 'POST'])
@login_required
def receipt_settings():
    form = POSReceiptSettingsForm()
    
    # Try to get existing settings, handle missing columns gracefully
    try:
        settings = POSReceiptSettings.query.first()
    except Exception as e:
        # If there's an error with the query, likely due to missing columns
        print(f"Error querying receipt settings: {e}")
        # Create a new settings object without querying the database
        settings = POSReceiptSettings(
            header_text="Thank you for shopping with us!",
            footer_text="Please come again!",
            show_logo=True,
            show_cashier=True,
            show_tax_details=True,
            show_barcode=True,
            show_qr_code=True,
            show_customer=True
        )
    
    if not settings:
        settings = POSReceiptSettings(
            header_text="Thank you for shopping with us!",
            footer_text="Please come again!",
            show_logo=True,
            show_cashier=True,
            show_tax_details=True,
            show_barcode=True,
            show_qr_code=True,
            show_customer=True
        )
        try:
            db.session.add(settings)
            db.session.commit()
        except Exception as e:
            print(f"Error creating new settings: {e}")
            db.session.rollback()
    
    if form.validate_on_submit():
        try:
            settings.header_text = form.header_text.data
            settings.footer_text = form.footer_text.data
            settings.company_name = form.company_name.data
            settings.company_address = form.company_address.data
            settings.company_phone = form.company_phone.data
            settings.show_logo = form.show_logo.data
            settings.show_cashier = form.show_cashier.data
            settings.show_tax_details = form.show_tax_details.data
            
            # Handle new fields that might not exist in the database yet
            try:
                settings.show_barcode = form.show_barcode.data
                settings.show_qr_code = form.show_qr_code.data
                settings.show_customer = form.show_customer.data
            except Exception:
                pass
            
            # Handle logo upload
            if form.company_logo.data:
                import os
                from werkzeug.utils import secure_filename
                
                # Make sure the upload directory exists
                upload_dir = os.path.join('static', 'uploads', 'logos')
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                
                # Save the uploaded file
                filename = secure_filename(form.company_logo.data.filename)
                file_path = os.path.join(upload_dir, filename)
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                form.company_logo.data.save(file_path)
                settings.logo_path = f'/static/uploads/logos/{filename}'
            
            db.session.commit()
            flash('Receipt settings updated successfully!', 'success')
        except Exception as e:
            print(f"Error updating settings: {e}")
            db.session.rollback()
            flash(f'Error updating settings: {str(e)}', 'danger')
        
        return redirect(url_for('pos.receipt_settings'))
    
    elif request.method == 'GET':
        form.header_text.data = settings.header_text
        form.footer_text.data = settings.footer_text
        
        # Set company information fields
        try:
            form.company_name.data = settings.company_name
            form.company_address.data = settings.company_address
            form.company_phone.data = settings.company_phone
        except Exception:
            form.company_name.data = "YOUR COMPANY NAME"
            form.company_address.data = "123 Main Street, Accra, Ghana"
            form.company_phone.data = "+233 123 456 789"
        
        form.show_logo.data = settings.show_logo
        form.show_cashier.data = settings.show_cashier
        form.show_tax_details.data = settings.show_tax_details
        
        # Handle new fields that might not exist in the database yet
        try:
            form.show_barcode.data = settings.show_barcode
            form.show_qr_code.data = settings.show_qr_code
            form.show_customer.data = settings.show_customer
        except Exception:
            form.show_barcode.data = True
            form.show_qr_code.data = True
            form.show_customer.data = True
    
    # Pass current date and time to the template
    from datetime import datetime
    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # Create a simplified settings object for the template if we can't use the database one
    template_settings = {
        'logo_path': getattr(settings, 'logo_path', None)
    }
    
    return render_template('pos/receipt_settings.html', form=form, settings=template_settings, current_datetime=current_datetime)

# POS General Settings
@pos.route('/settings', methods=['GET', 'POST'])
@login_required
def pos_settings():
    form = POSSettingsForm()
    settings = POSSettings.query.first()
    
    if not settings:
        settings = POSSettings(
            currency_symbol="GH₵",
            default_customer_id=1,
            allow_negative_stock=False,
            restrict_price_edit=True,
            auto_print_receipt=True
        )
        db.session.add(settings)
        db.session.commit()
    
    if form.validate_on_submit():
        settings.currency_symbol = form.currency_symbol.data
        settings.default_customer_id = form.default_customer_id.data
        settings.allow_negative_stock = form.allow_negative_stock.data
        settings.restrict_price_edit = form.restrict_price_edit.data
        settings.auto_print_receipt = form.auto_print_receipt.data
        
        db.session.commit()
        flash('POS settings updated successfully!', 'success')
        return redirect(url_for('pos.pos_settings'))
    
    elif request.method == 'GET':
        form.currency_symbol.data = settings.currency_symbol
        form.default_customer_id.data = settings.default_customer_id
        form.allow_negative_stock.data = settings.allow_negative_stock
        form.restrict_price_edit.data = settings.restrict_price_edit
        form.auto_print_receipt.data = settings.auto_print_receipt
    
    return render_template('pos/settings.html', form=form)

# API endpoints for POS terminal
@pos.route('/api/products')
@login_required
def api_products():
    """API endpoint to get products for POS terminal"""
    try:
        # Force a fresh query to get the latest data
        db.session.expire_all()
        
        products = Product.query.filter_by(is_active=True).all()
        
        result = []
        
        for product in products:
            # Ensure we get the latest available_quantity
            db.session.refresh(product)
            
            result.append({
                'id': product.id,
                'name': product.name,
                'price': product.sale_price,
                'image': product.image_path or '/static/img/no-image.png',
                'category_id': product.category_id,
                'barcode': product.barcode,
                'available_quantity': product.available_quantity,
                'product_type': product.product_type
            })
        
        return jsonify({'success': True, 'products': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@pos.route('/api/create-order', methods=['POST'])
@login_required
def api_create_order():
    """API endpoint to create a new POS order"""
    try:
        # Get JSON data from request
        data = request.get_json()
        print("Received order data:", data)
        
        if not data:
            print("No JSON data received, checking for form data")
            # Try to get form data if JSON parsing failed
            data = request.form.to_dict()
            if not data:
                print("No form data either, checking raw data")
                try:
                    raw_data = request.data.decode('utf-8')
                    print(f"Raw request data: {raw_data}")
                    import json
                    data = json.loads(raw_data)
                except Exception as parse_error:
                    print(f"Failed to parse raw data: {str(parse_error)}")
                    return jsonify({'success': False, 'message': 'Invalid data format. Please check your request.'})
        
        # Check if there's an active session for the current user
        active_session = POSSession.query.filter_by(user_id=current_user.id, state='open').first()
        
        if not active_session:
            return jsonify({'success': False, 'message': 'No active POS session found.'})
        
        # Check if this is an exchange from a return
        exchange_return_id = data.get('exchange_return_id')
        exchange_return = None
        exchange_credit = 0
        
        if exchange_return_id:
            exchange_return = POSReturn.query.get(exchange_return_id)
            if exchange_return and exchange_return.state == 'validated' and exchange_return.refund_method == 'exchange':
                exchange_credit = exchange_return.total_amount
                print(f"Processing exchange for return #{exchange_return.name} with credit: {exchange_credit}")
        
        # Create new order
        order = POSOrder(
            name=f'POS/{datetime.utcnow().strftime("%Y%m%d")}/{active_session.id}/{POSOrder.query.count() + 1}',
            session_id=active_session.id,
            customer_id=data.get('customer_id'),
            payment_method=data.get('payment_method', 'cash'),
            payment_reference=data.get('payment_reference', ''),
            state='paid',
            created_by=current_user.id
        )
        
        # If the user has an associated employee, link the order to that employee
        from modules.employees.models import Employee
        employee = Employee.query.filter_by(user_id=current_user.id).first()
        if employee:
            order.employee_id = employee.id
        
        # Add order to database first to get an ID
        db.session.add(order)
        db.session.flush()
        
        # Create order lines
        total_amount = 0
        tax_amount = 0
        
        # The frontend sends 'items' but the backend was looking for 'products'
        for product_data in data.get('items', []):
            product_id = product_data.get('product_id')
            quantity = float(product_data.get('quantity', 1) or 1)  # Default to 1 if None
            
            # The frontend sends 'price' but the model uses 'unit_price'
            price = float(product_data.get('price') or 0)  # Default to 0 if None
            if price == 0:
                # Try the unit_price field as a fallback
                price = float(product_data.get('unit_price') or 0)
            
            # Get product from database
            product = Product.query.get(product_id)
            
            if not product:
                return jsonify({'success': False, 'message': f'Product with ID {product_id} not found.'})
            
            # Check if product has enough stock
            if product.product_type == 'storable' and not active_session.cash_register.pos_settings.allow_negative_stock:
                shop_location = StockLocation.query.filter_by(code='SHOP').first()
                
                if not shop_location:
                    return jsonify({'success': False, 'message': 'Shop location not found.'})
                
                available_qty = product.get_available_quantity(shop_location.id)
                
                if available_qty < quantity:
                    return jsonify({
                        'success': False, 
                        'message': f'Not enough stock for product {product.name}. Available: {available_qty}, Requested: {quantity}'
                    })
            
            # Create order line
            order_line = POSOrderLine(
                order_id=order.id,
                product_id=product_id,
                description=product.name,
                quantity=quantity,
                unit_price=price,
                discount_percent=0,
                tax_percent=10  # Default tax rate
            )
            
            # Calculate line totals
            line_subtotal = quantity * price
            line_tax = line_subtotal * 0.1  # 10% tax
            
            total_amount += line_subtotal
            tax_amount += line_tax
            
            # Debug the line totals
            print(f"Line: {product.name}, Qty: {quantity}, Price: {price}, Subtotal: {line_subtotal}")
            
            order.lines.append(order_line)
        
        # Update order totals with the calculated values
        order.total_amount = total_amount
        order.tax_amount = tax_amount
        
        # Print debug information
        print(f"Order {order.name} - Total Amount: {total_amount}, Tax Amount: {tax_amount}")
        
        # Apply exchange credit if applicable
        if exchange_return and exchange_credit > 0:
            # Add a note about the exchange
            if order.notes:
                order.notes += f"\nExchange from return #{exchange_return.name} with credit: ₵{exchange_credit:.2f}"
            else:
                order.notes = f"Exchange from return #{exchange_return.name} with credit: ₵{exchange_credit:.2f}"
            
            # Update the exchange return to link it to this order
            exchange_return.notes = f"{exchange_return.notes}\nExchanged for order: {order.name}" if exchange_return.notes else f"Exchanged for order: {order.name}"
            
            # If the exchange credit is greater than or equal to the total, no payment is needed
            if exchange_credit >= total_amount:
                order.payment_method = 'exchange_credit'
                order.payment_reference = f"Full exchange from return #{exchange_return.name}"
                
                # If there's remaining credit (change to give back to customer)
                if exchange_credit > total_amount:
                    remaining_credit = exchange_credit - total_amount
                    exchange_return.notes += f"\nRemaining credit: ₵{remaining_credit:.2f} given as change"
                    # Mark the exchange return as fully used - the remaining amount is given as change
                    exchange_return.total_amount = 0
                    exchange_return.state = 'completed'
                    exchange_return.notes += f"\nExchange completed with change given: ₵{remaining_credit:.2f}"
                else:
                    # Exact amount exchange
                    exchange_return.total_amount = 0
                    exchange_return.state = 'completed'
                    exchange_return.notes += "\nExchange completed with exact amount"
            else:
                # Partial payment with exchange credit
                order.payment_reference = f"Partial exchange from return #{exchange_return.name}, remaining paid with {order.payment_method}"
                # The exchange return is fully used
                exchange_return.total_amount = 0
                exchange_return.state = 'completed'
                exchange_return.notes += "\nExchange completed with additional payment"
        
        # Commit changes
        db.session.commit()
        
        # Create stock moves for the order
        order.create_stock_moves()
        
        # Explicitly refresh the database session to ensure latest data
        db.session.expire_all()
        
        # Refresh product objects to update available_quantity
        for product_data in data.get('items', []):
            product = Product.query.get(product_data.get('product_id'))
            if product:
                db.session.refresh(product)
        
        return jsonify({
            'success': True, 
            'message': 'Order created successfully', 
            'order_id': order.id,
            'receipt_url': url_for('pos.view_receipt', order_id=order.id),
            'receipt_print_url': url_for('pos.print_receipt', order_id=order.id)
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Error creating order: {str(e)}")
        print(f"Traceback: {error_traceback}")
        
        # Return a more detailed error message for debugging
        return jsonify({
            'success': False, 
            'message': f'An error occurred while processing your order: {str(e)}',
            'error_type': type(e).__name__
        })

# Generate Sales Report
@pos.route('/sessions/<int:session_id>/report')
@login_required
def session_report(session_id):
    """Display session sales report"""
    session = POSSession.query.get_or_404(session_id)
    
    # Check if user has access to this session
    if session.user_id != current_user.id and not current_user.has_role('Admin'):
        flash('You do not have permission to view this session report.', 'danger')
        return redirect(url_for('pos.sessions'))
    
    # Get all orders for this session
    orders = POSOrder.query.filter_by(session_id=session_id).all()
    
    # Calculate report date (use the latest order date or session date)
    if orders:
        report_date = max(order.order_date for order in orders)
    else:
        report_date = session.start_time
    
    # Get all order lines
    order_lines = []
    for order in orders:
        for line in order.lines:
            order_lines.append(line)
    
    # Organize sales by category
    sales_by_category = defaultdict(list)
    category_totals = defaultdict(lambda: {'qty': 0, 'amount': 0})
    
    for line in order_lines:
        category_name = "Uncategorized" if not line.product else (line.product.category.name if line.product.category else "Uncategorized")
        
        # Add to category products
        product_exists = False
        for product in sales_by_category[category_name]:
            if product.product_id == line.product_id:
                product.qty += line.quantity
                product.amount += line.quantity * line.unit_price
                product_exists = True
                break
        
        if not product_exists:
            class ProductSummary:
                def __init__(self, product_id, name, qty, amount):
                    self.product_id = product_id
                    self.name = name
                    self.qty = qty
                    self.amount = amount
            
            sales_by_category[category_name].append(
                ProductSummary(
                    line.product_id,
                    line.product.name if line.product else "Unknown Product",
                    line.quantity,
                    line.quantity * line.unit_price
                )
            )
        
        # Update category totals
        category_totals[category_name]['qty'] += line.quantity
        category_totals[category_name]['amount'] += line.quantity * line.unit_price
    
    # Calculate totals
    total_qty = sum(category_totals[category]['qty'] for category in category_totals)
    total_amount = sum(category_totals[category]['amount'] for category in category_totals)
    
    # Calculate tax
    tax_rate = 15  # Assuming 15% tax rate
    tax_amount = sum(order.tax_amount for order in orders)
    total_with_tax = total_amount + tax_amount
    
    # Calculate payments by method
    payments = defaultdict(float)
    for order in orders:
        payment_method = order.payment_method.capitalize()
        if order.payment_method == 'momo':
            payment_method = 'Mobile Money'
        payments[f"{payment_method}"] += order.total_amount
    
    # Discounts (placeholder for now)
    discounts_count = 0
    discounts_amount = 0.0
    
    # Transactions count
    transactions_count = len(orders)
    
    # Get the sales worker information
    sales_worker = User.query.get(session.user_id)
    
    # Check if it's a download request
    if request.args.get('download') == 'pdf':
        return render_template(
            'pos/sales_report.html',
            session=session,
            report_date=report_date,
            sales_by_category=sales_by_category,
            category_totals=category_totals,
            total_qty=total_qty,
            total_amount=total_amount,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            total_with_tax=total_with_tax,
            payments=payments,
            discounts_count=discounts_count,
            discounts_amount=discounts_amount,
            transactions_count=transactions_count,
            sales_worker=sales_worker,
            print_mode=True
        )
    
    # Regular session report view
    return render_template(
        'pos/session_report.html',
        session=session,
        report_date=report_date,
        sales_by_category=sales_by_category,
        category_totals=category_totals,
        total_qty=total_qty,
        total_amount=total_amount,
        tax_rate=tax_rate,
        tax_amount=tax_amount,
        total_with_tax=total_with_tax,
        payment_methods=payments,
        discounts_count=discounts_count,
        discounts_amount=discounts_amount,
        total_orders=transactions_count,
        total_sales=total_with_tax,
        orders=orders
    )

# Download Sales Report as HTML (printable)
@pos.route('/sessions/<int:session_id>/report/download')
@login_required
def download_session_report(session_id):
    """Download session sales report"""
    session = POSSession.query.get_or_404(session_id)
    
    # Check if user has access to this session
    if session.user_id != current_user.id and not current_user.has_role('Admin'):
        flash('You do not have permission to download this session report.', 'danger')
        return redirect(url_for('pos.sessions'))
    
    # Get all orders for this session
    orders = POSOrder.query.filter_by(session_id=session_id).all()
    
    # Calculate report date (use the latest order date or session date)
    if orders:
        report_date = max(order.order_date for order in orders)
    else:
        report_date = session.start_time
    
    # Get all order lines
    order_lines = []
    for order in orders:
        for line in order.lines:
            order_lines.append(line)
    
    # Organize sales by category
    sales_by_category = defaultdict(list)
    category_totals = defaultdict(lambda: {'qty': 0, 'amount': 0})
    
    for line in order_lines:
        category_name = "Uncategorized" if not line.product else (line.product.category.name if line.product.category else "Uncategorized")
        
        # Add to category products
        product_exists = False
        for product in sales_by_category[category_name]:
            if product.product_id == line.product_id:
                product.qty += line.quantity
                product.amount += line.quantity * line.unit_price
                product_exists = True
                break
        
        if not product_exists:
            class ProductSummary:
                def __init__(self, product_id, name, qty, amount):
                    self.product_id = product_id
                    self.name = name
                    self.qty = qty
                    self.amount = amount
            
            sales_by_category[category_name].append(
                ProductSummary(
                    line.product_id,
                    line.product.name if line.product else "Unknown Product",
                    line.quantity,
                    line.quantity * line.unit_price
                )
            )
        
        # Update category totals
        category_totals[category_name]['qty'] += line.quantity
        category_totals[category_name]['amount'] += line.quantity * line.unit_price
    
    # Calculate totals
    total_qty = sum(category_totals[category]['qty'] for category in category_totals)
    total_amount = sum(category_totals[category]['amount'] for category in category_totals)
    
    # Calculate tax
    tax_rate = 15  # Assuming 15% tax rate
    tax_amount = sum(order.tax_amount for order in orders)
    total_with_tax = total_amount + tax_amount
    
    # Calculate payments by method
    payments = defaultdict(float)
    for order in orders:
        payment_method = order.payment_method.capitalize()
        if order.payment_method == 'momo':
            payment_method = 'Mobile Money'
        payments[f"{payment_method}"] += order.total_amount
    
    # Discounts (placeholder for now)
    discounts_count = 0
    discounts_amount = 0.0
    
    # Transactions count
    transactions_count = len(orders)
    
    # Get the sales worker information
    sales_worker = User.query.get(session.user_id)
    
    # Render the template with print_mode=True
    html = render_template(
        'pos/session_report.html',
        session=session,
        report_date=report_date,
        sales_by_category=sales_by_category,
        category_totals=category_totals,
        total_qty=total_qty,
        total_amount=total_amount,
        tax_rate=tax_rate,
        tax_amount=tax_amount,
        total_with_tax=total_with_tax,
        payment_methods=payments,
        discounts_count=discounts_count,
        discounts_amount=discounts_amount,
        total_orders=transactions_count,
        total_sales=total_with_tax,
        orders=orders,
        print_mode=True
    )
    
    # Create a response with the HTML content
    response = make_response(html)
    
    # Set headers for HTML download
    response.headers['Content-Type'] = 'text/html'
    response.headers['Content-Disposition'] = f'attachment; filename=sales_report_{session.id}_{date.today().strftime("%Y%m%d")}.html'
    
    return response

# Returns Management Routes
@pos.route('/returns')
@login_required
def returns():
    """List all returns"""
    try:
        # Get filter parameters
        state_filter = request.args.get('state', None)
        
        # Base query
        query = POSReturn.query.order_by(POSReturn.return_date.desc())
        
        # Apply filters if provided
        if state_filter:
            query = query.filter(POSReturn.state == state_filter)
        
        # For salesworkers (non-admin/non-manager users), only show returns they created
        from modules.auth.models import User
        user = User.query.get(current_user.id)
        is_admin = user.has_role('Admin')
        is_manager = user.has_role('Manager')
        
        if not is_admin and not is_manager:
            query = query.filter(POSReturn.created_by == current_user.id)
        
        # Execute query
        returns = query.all()
        
        return render_template('pos/returns.html', returns=returns, current_filter=state_filter)
    except Exception as e:
        # If the table doesn't exist, create it
        with db.engine.connect() as conn:
            # Drop existing tables if they exist
            conn.execute(db.text('DROP TABLE IF EXISTS quality_checks'))
            conn.execute(db.text('DROP TABLE IF EXISTS pos_return_lines'))
            conn.execute(db.text('DROP TABLE IF EXISTS pos_returns'))
            
            # Create tables with correct schema
            conn.execute(db.text('''
                CREATE TABLE IF NOT EXISTS pos_returns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(64) UNIQUE,
                    original_order_id INTEGER,
                    customer_name VARCHAR(128),
                    customer_phone VARCHAR(64),
                    return_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_amount FLOAT DEFAULT 0.0,
                    refund_amount FLOAT DEFAULT 0.0,
                    return_type VARCHAR(20),
                    refund_method VARCHAR(20),
                    notes TEXT,
                    state VARCHAR(20) DEFAULT 'draft',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    FOREIGN KEY (original_order_id) REFERENCES pos_orders (id)
                )
            '''))
            
            conn.execute(db.text('''
                CREATE TABLE IF NOT EXISTS pos_return_lines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    return_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    return_reason VARCHAR(64),
                    quantity FLOAT DEFAULT 0.0,
                    unit_price FLOAT DEFAULT 0.0,
                    subtotal FLOAT DEFAULT 0.0,
                    state VARCHAR(20) DEFAULT 'draft',
                    FOREIGN KEY (return_id) REFERENCES pos_returns (id),
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            '''))
            
            conn.execute(db.text('''
                CREATE TABLE IF NOT EXISTS quality_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(64) UNIQUE,
                    return_line_id INTEGER NOT NULL,
                    quality_state VARCHAR(20) DEFAULT 'pending',
                    disposition VARCHAR(20),
                    notes TEXT,
                    checked_by INTEGER,
                    check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (return_line_id) REFERENCES pos_return_lines (id),
                    FOREIGN KEY (checked_by) REFERENCES users (id)
                )
            '''))
            
        # Now try to query again
        returns = POSReturn.query.order_by(POSReturn.return_date.desc()).all()
        flash('Returns management system has been initialized.', 'success')
        return render_template('pos/returns.html', returns=returns)

@pos.route('/returns/new', methods=['GET', 'POST'])
@login_required
def new_return():
    """Create a new return"""
    if request.method == 'POST':
        try:
            # Get form data
            original_order_id = request.form.get('original_order_id')
            
            # Validate that an original order is selected
            if not original_order_id:
                raise ValueError("An original order must be selected for all returns")
                
            original_order_id = int(original_order_id) if original_order_id else None
            customer_name = request.form.get('customer_name')
            customer_phone = request.form.get('customer_phone')
            return_type = request.form.get('return_type')
            refund_method = request.form.get('refund_method')
            notes = request.form.get('notes')
            
            # Get product data from form
            product_ids = request.form.getlist('product_id[]')
            quantities = request.form.getlist('quantity[]')
            prices = request.form.getlist('price[]')
            return_reasons = request.form.getlist('return_reason[]')
            line_notes = request.form.getlist('line_notes[]')
            original_line_ids = request.form.getlist('original_line_id[]')
            
            # Validate that at least one product is selected
            if not product_ids or not any(product_ids):
                raise ValueError("At least one product must be selected for return")
                
            # Create return
            pos_return = POSReturn(
                original_order_id=original_order_id,
                customer_name=customer_name,
                customer_phone=customer_phone,
                return_type=return_type,
                refund_method=refund_method,
                notes=notes,
                state='draft',
                created_by=current_user.id
            )
            
            # Get the original order
            original_order = POSOrder.query.get(original_order_id)
            if not original_order:
                raise ValueError("Original order not found")
            
            # Track total return amount
            total_amount = 0.0
            
            # Process return lines
            for i in range(len(product_ids)):
                if not product_ids[i]:
                    continue  # Skip empty product IDs
                    
                product_id = int(product_ids[i])
                
                # Verify the product exists
                product = Product.query.get(product_id)
                if not product:
                    raise ValueError(f"Product with ID {product_id} does not exist")
                
                quantity = int(float(quantities[i])) if i < len(quantities) else 1  # Convert to integer
                price = float(prices[i]) if i < len(prices) else 0.0
                
                # Safely get return reason, default to empty string if index out of range
                return_reason = return_reasons[i] if i < len(return_reasons) else ""
                
                # Safely get line note, default to empty string if index out of range
                note = line_notes[i] if i < len(line_notes) else ""
                
                # Find all order lines for this product with returnable quantity
                order_lines = POSOrderLine.query.filter_by(
                    order_id=original_order_id,
                    product_id=product_id
                ).all()
                
                # Filter to only include lines with returnable quantity
                returnable_lines = [line for line in order_lines if line.returnable_quantity > 0]
                
                if not returnable_lines:
                    raise ValueError(
                        f"Product {product.name} has no returnable quantity left in this order."
                    )
                
                # Calculate total returnable quantity for this product
                total_returnable = sum(line.returnable_quantity for line in returnable_lines)
                
                if quantity > total_returnable:
                    raise ValueError(
                        f"Cannot return {quantity} units of {product.name}. "
                        f"The maximum returnable quantity is {int(total_returnable)} units."
                    )
                
                # Distribute the return quantity across the available order lines
                remaining_quantity = quantity
                for line in returnable_lines:
                    if remaining_quantity <= 0:
                        break
                        
                    # Calculate how much to return from this line
                    line_return_quantity = min(remaining_quantity, line.returnable_quantity)
                    remaining_quantity -= line_return_quantity
                    
                    # Create a return line for this portion
                    line_subtotal = price * line_return_quantity
                    total_amount += line_subtotal
                    
                    return_line = POSReturnLine(
                        product_id=product_id,
                        quantity=line_return_quantity,
                        unit_price=price,
                        subtotal=line_subtotal,
                        return_reason=return_reason,
                        state='draft',
                        original_order_line_id=line.id
                    )
                    pos_return.return_lines.append(return_line)
            
            pos_return.total_amount = total_amount
            pos_return.refund_amount = total_amount if refund_method != 'exchange' else 0
            
            # Generate a unique name for the return
            pos_return.generate_name()
            
            db.session.add(pos_return)
            db.session.commit()
            
            flash('Return created successfully', 'success')
            return redirect(url_for('pos.return_detail', return_id=pos_return.id))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating return: {str(e)}")
            flash(f'Error creating return: {str(e)}', 'danger')
    
    # Since employee_id is not set on orders, we need to use created_by instead
    # Get returnable orders using a direct SQL query
    returnable_orders_query = """
    SELECT DISTINCT o.id FROM pos_orders o
    JOIN pos_order_lines l ON l.order_id = o.id
    WHERE o.state = 'paid'
    AND l.quantity > l.returned_quantity
    AND NOT EXISTS (
        SELECT 1 FROM pos_returns r
        WHERE r.original_order_id = o.id
        AND r.state IN ('draft', 'validated')
    )
    AND o.created_by = :user_id
    ORDER BY o.order_date DESC
    LIMIT 100
    """
    
    # Execute the query with the current user's ID
    returnable_order_ids = [
        row[0] for row in db.session.execute(
            text(returnable_orders_query), 
            {'user_id': current_user.id}
        ).fetchall()
    ]
    
    # Then load the actual order objects
    returnable_orders = POSOrder.query.filter(POSOrder.id.in_(returnable_order_ids)).order_by(POSOrder.order_date.desc()).all()
    
    print(f"Found {len(returnable_orders)} returnable orders for user {current_user.username} (ID: {current_user.id})")
    
    # Debug: Print order return status for the filtered orders
    for order in returnable_orders:
        print(f"Order {order.name}: created_by = {order.created_by}")
        for line in order.lines:
            print(f"  Line {line.id}: quantity = {line.quantity}, returned_quantity = {line.returned_quantity}, returnable_quantity = {line.returnable_quantity}")
    
    return render_template('pos/return_form.html', orders=returnable_orders)

@pos.route('/returns/<int:return_id>')
@login_required
def return_detail(return_id):
    """View return details"""
    pos_return = POSReturn.query.get_or_404(return_id)
    return render_template('pos/return_detail.html', return_=pos_return)

@pos.route('/returns/<int:return_id>/validate', methods=['POST'])
@login_required
def validate_return(return_id):
    """Validate a return"""
    pos_return = POSReturn.query.get_or_404(return_id)
    
    if pos_return.validate_return():
        flash('Return validated successfully', 'success')
        
        # If the return is for an exchange, redirect to POS terminal
        if pos_return.refund_method == 'exchange':
            # Check if there's an active session
            active_session = POSSession.query.filter_by(user_id=current_user.id, state='open').first()
            
            if not active_session:
                flash('You need an open POS session to process an exchange. Please open a session first.', 'warning')
                return redirect(url_for('pos.new_session', next=url_for('pos.terminal_unified', exchange_return_id=return_id)))
            
            # Store the return ID in the session for the POS terminal to use
            return redirect(url_for('pos.terminal_unified', exchange_return_id=return_id))
    else:
        flash('Error validating return', 'danger')
        
    return redirect(url_for('pos.return_detail', return_id=return_id))

@pos.route('/returns/<int:return_id>/cancel', methods=['POST'])
@login_required
def cancel_return(return_id):
    """Cancel a return"""
    pos_return = POSReturn.query.get_or_404(return_id)
    
    if pos_return.state == 'draft':
        pos_return.state = 'cancelled'
        db.session.commit()
        flash('Return cancelled successfully', 'success')
    else:
        flash('Cannot cancel a validated return', 'danger')
        
    return redirect(url_for('pos.return_detail', return_id=return_id))

@pos.route('/quality-checks')
@login_required
def quality_checks():
    """List all quality checks"""
    from modules.auth.models import User
    user = User.query.get(current_user.id)
    is_admin = user.has_role('admin')
    
    if is_admin:
        # Admins can see all quality checks
        checks = QualityCheck.query.order_by(QualityCheck.check_date.desc()).all()
    else:
        # Salesworkers can only see quality checks for returns they created
        checks = QualityCheck.query.join(
            POSReturnLine, QualityCheck.return_line_id == POSReturnLine.id
        ).join(
            POSReturn, POSReturnLine.return_id == POSReturn.id
        ).filter(
            POSReturn.created_by == current_user.id
        ).order_by(QualityCheck.check_date.desc()).all()
    
    return render_template('pos/quality_checks.html', checks=checks)

@pos.route('/quality-checks/new/<int:return_line_id>', methods=['GET', 'POST'])
@login_required
def new_quality_check(return_line_id):
    """Create a new quality check"""
    return_line = POSReturnLine.query.get_or_404(return_line_id)
    
    if request.method == 'POST':
        try:
            quality_state = request.form.get('quality_state')
            disposition = request.form.get('disposition')
            notes = request.form.get('notes')
            
            # Get the quantity being checked (default to full quantity if not specified)
            try:
                check_quantity = float(request.form.get('check_quantity', return_line.quantity))
                # Ensure quantity is valid
                if check_quantity <= 0 or check_quantity > return_line.quantity:
                    check_quantity = return_line.quantity
            except (ValueError, TypeError):
                check_quantity = return_line.quantity
            
            quality_check = QualityCheck(
                return_line_id=return_line_id,
                checked_by=current_user.id,
                quality_state=quality_state,
                disposition=disposition,
                notes=notes,
                quantity=check_quantity,
                check_date=datetime.now()
            )
            
            db.session.add(quality_check)
            db.session.commit()
            
            # Process the quality check result
            quality_check.process_result()
            
            flash('Quality check completed successfully', 'success')
            return redirect(url_for('pos.return_detail', return_id=return_line.return_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating quality check: {str(e)}', 'danger')
    
    return render_template('pos/quality_check_form.html', return_line=return_line)

@pos.route('/sequential-quality-checks')
@pos.route('/sequential-quality-checks/<int:return_id>')
@login_required
def sequential_quality_checks(return_id=None):
    """Process quality checks sequentially"""
    # Check if user is admin
    from modules.auth.models import User
    user = User.query.get(current_user.id)
    is_admin = user.has_role('admin')
    
    # Base query for pending lines
    base_query = db.session.query(POSReturnLine).outerjoin(
        QualityCheck, QualityCheck.return_line_id == POSReturnLine.id
    ).join(
        POSReturn, POSReturn.id == POSReturnLine.return_id
    ).filter(
        QualityCheck.id == None,  # No quality check exists yet
        POSReturnLine.state == 'pending',
        POSReturn.state == 'validated'  # Only show validated returns
    )
    
    # For non-admin users, only show returns they created
    if not is_admin:
        base_query = base_query.filter(POSReturn.created_by == current_user.id)
    
    # Get pending return lines that need quality checks
    if return_id:
        # Filter by specific return
        pending_lines = base_query.filter(POSReturnLine.return_id == return_id).all()
        
        # Get the return object to display its name
        pos_return = POSReturn.query.get_or_404(return_id)
        
        # Check if the user has permission to view this return
        if not is_admin and pos_return.created_by != current_user.id:
            flash('You do not have permission to view this return.', 'danger')
            return redirect(url_for('pos.returns'))
            
        return_filter = f"Return #{pos_return.id}"
    else:
        # Get all pending lines from all returns (filtered by user if not admin)
        pending_lines = base_query.all()
        return_filter = "All Returns"
    
    # Get completed quality checks (filtered by user if not admin)
    if is_admin:
        completed_checks = QualityCheck.query.all()
    else:
        completed_checks = QualityCheck.query.join(
            POSReturnLine, QualityCheck.return_line_id == POSReturnLine.id
        ).join(
            POSReturn, POSReturnLine.return_id == POSReturn.id
        ).filter(
            POSReturn.created_by == current_user.id
        ).all()
    
    return render_template(
        'pos/sequential_quality_checks.html',
        pending_lines=pending_lines,
        completed_checks=completed_checks,
        return_filter=return_filter,
        return_id=return_id
    )

@pos.route('/return/<int:return_id>/quality-checks')
@login_required
def return_quality_checks(return_id):
    """Display quality checks for a specific return"""
    pos_return = POSReturn.query.get_or_404(return_id)
    
    # Check if user is admin or the creator of this return
    from modules.auth.models import User
    user = User.query.get(current_user.id)
    is_admin = user.has_role('admin')
    
    # Check if the user has permission to view this return
    if not is_admin and pos_return.created_by != current_user.id:
        flash('You do not have permission to view quality checks for this return.', 'danger')
        return redirect(url_for('pos.returns'))
    
    # Get pending return lines that need quality checks
    pending_lines = db.session.query(POSReturnLine).outerjoin(
        QualityCheck, QualityCheck.return_line_id == POSReturnLine.id
    ).filter(
        POSReturnLine.return_id == return_id,
        QualityCheck.id == None,
        POSReturnLine.state == 'pending'
    ).all()
    
    # Get completed quality checks for this return
    completed_checks = QualityCheck.query.join(
        POSReturnLine, QualityCheck.return_line_id == POSReturnLine.id
    ).filter(
        POSReturnLine.return_id == return_id
    ).all()
    
    return render_template(
        'pos/return_quality_checks.html',
        pos_return=pos_return,
        pending_lines=pending_lines,
        completed_checks=completed_checks
    )

@pos.route('/quality-dashboard')
@login_required
def quality_dashboard():
    """Quality control dashboard"""
    # Get stats for the dashboard
    total_returns = db.session.query(func.count(POSReturn.id)).scalar() or 0
    
    # Get quality check stats
    resellable_count = db.session.query(func.count(QualityCheck.id)).filter(
        QualityCheck.quality_state.in_(['pass', 'not_defective'])
    ).scalar() or 0
    
    defective_count = db.session.query(func.count(QualityCheck.id)).filter(
        QualityCheck.quality_state.in_(['minor_defect', 'major_defect'])
    ).scalar() or 0
    
    # Get pending returns that need quality checks
    pending_count = db.session.query(func.count(POSReturnLine.id)).outerjoin(
        QualityCheck, QualityCheck.return_line_id == POSReturnLine.id
    ).filter(QualityCheck.id == None).scalar() or 0
    
    # Get returns that need validation (in draft state)
    unvalidated_returns_count = db.session.query(func.count(POSReturn.id)).filter(
        POSReturn.state == 'draft'
    ).scalar() or 0
    
    # Get actual pending return lines for display
    pending_returns = db.session.query(POSReturnLine).outerjoin(
        QualityCheck, QualityCheck.return_line_id == POSReturnLine.id
    ).filter(
        QualityCheck.id == None
    ).order_by(POSReturnLine.id.desc()).limit(10).all()
    
    # Calculate percentages
    total_checked = resellable_count + defective_count
    resellable_percentage = (resellable_count / total_checked * 100) if total_checked > 0 else 0
    defective_percentage = (defective_count / total_checked * 100) if total_checked > 0 else 0
    
    # Get recent quality checks
    recent_checks = QualityCheck.query.order_by(QualityCheck.check_date.desc()).limit(5).all()
    
    # Get top products with quality issues
    top_defective_products = []
    # This would be a more complex query in a real system
    
    return render_template('pos/quality_dashboard.html', 
                           total_returns=total_returns,
                           resellable_count=resellable_count,
                           defective_count=defective_count,
                           pending_count=pending_count,
                           pending_returns=pending_returns,
                           resellable_percentage=resellable_percentage,
                           defective_percentage=defective_percentage,
                           recent_checks=recent_checks,
                           top_defective_products=top_defective_products,
                           unvalidated_returns_count=unvalidated_returns_count)

@pos.route('/process-quality-check/<int:return_line_id>', methods=['POST'])
@login_required
def process_quality_check(return_line_id):
    """Process a quality check for a return line"""
    return_line = POSReturnLine.query.get_or_404(return_line_id)
    
    # Get form data
    quality_state = request.form.get('quality_state')
    disposition = request.form.get('disposition')
    notes = request.form.get('notes')
    return_id = request.form.get('return_id')
    
    # Get the quantity being checked (default to full quantity if not specified)
    try:
        check_quantity = float(request.form.get('check_quantity', return_line.quantity))
        # Ensure quantity is valid
        if check_quantity <= 0 or check_quantity > return_line.quantity:
            check_quantity = return_line.quantity
    except (ValueError, TypeError):
        check_quantity = return_line.quantity
    
    # Create quality check
    quality_check = QualityCheck(
        return_line_id=return_line_id,
        checked_by=current_user.id,
        quality_state=quality_state,
        disposition=disposition,
        notes=notes,
        quantity=check_quantity,
        check_date=datetime.now()
    )
    
    db.session.add(quality_check)
    db.session.flush()  # Flush to get the ID but don't commit yet
    
    try:
        # Process the quality check result
        quality_check.process_result()
        
        # Commit changes
        db.session.commit()
        
        # Flash message
        flash(f'Quality check processed for {check_quantity} units of {return_line.product.name}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error processing quality check: {str(e)}', 'danger')
    
    # Redirect based on whether we have a return_id
    if return_id:
        return redirect(url_for('pos.sequential_quality_checks', return_id=return_id))
    else:
        return redirect(url_for('pos.sequential_quality_checks'))

@pos.route('/skip-quality-check/<int:return_line_id>')
@pos.route('/skip-quality-check/<int:return_line_id>/<int:return_id>')
@login_required
def skip_quality_check(return_line_id, return_id=None):
    """Skip a quality check and move to the next item"""
    # No actual processing needed, just redirect back to the sequential checks
    if return_id:
        return redirect(url_for('pos.sequential_quality_checks', return_id=return_id))
    else:
        return redirect(url_for('pos.sequential_quality_checks'))

@pos.route('/reports/returns')
@login_required
def returns_report():
    """Returns report"""
    # Filter parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    status = request.args.get('status')
    
    # Base query
    query = POSReturn.query
    
    # For sales workers, only show their own returns
    # For managers and admins, show all returns
    if not current_user.has_role('Admin') and not current_user.has_role('Manager'):
        query = query.filter(POSReturn.created_by == current_user.id)
    
    # Apply filters
    if start_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.filter(POSReturn.return_date >= start)
    
    if end_date:
        end = datetime.strptime(end_date, '%Y-%m-%d')
        end = end.replace(hour=23, minute=59, second=59)
        query = query.filter(POSReturn.return_date <= end)
    
    if status:
        query = query.filter(POSReturn.state == status)
    
    # Get results
    returns = query.order_by(POSReturn.return_date.desc()).all()
    
    # Calculate statistics
    total_returns = len(returns)
    total_refund_amount = sum(r.refund_amount for r in returns)
    
    # Count by reason
    reason_counts = {}
    for pos_return in returns:
        for line in pos_return.return_lines:
            reason = line.return_reason
            if reason in reason_counts:
                reason_counts[reason] += 1
            else:
                reason_counts[reason] = 1
    
    # Count by status
    status_counts = {
        'resellable': 0,
        'defective': 0,
        'pending': 0
    }
    
    for pos_return in returns:
        for line in pos_return.return_lines:
            if line.state in status_counts:
                status_counts[line.state] += 1
    
    # Count by customer
    customer_counts = {}
    for pos_return in returns:
        customer_name = pos_return.customer_name
        if not customer_name:
            customer_name = "Unknown Customer"
        
        if customer_name in customer_counts:
            customer_counts[customer_name] += 1
        else:
            customer_counts[customer_name] = 1
    
    # Sort and limit to top 10 customers
    sorted_customers = dict(sorted(customer_counts.items(), key=lambda item: item[1], reverse=True)[:10])
    
    # Count by disposition
    disposition_counts = {}
    
    # Get all quality checks related to these returns
    return_line_ids = []
    for pos_return in returns:
        for line in pos_return.return_lines:
            return_line_ids.append(line.id)
    
    quality_checks = QualityCheck.query.filter(QualityCheck.return_line_id.in_(return_line_ids)).all()
    
    for check in quality_checks:
        disposition = check.disposition or 'unknown'
        if disposition in disposition_counts:
            disposition_counts[disposition] += 1
        else:
            disposition_counts[disposition] = 1
    
    # Calculate potential recovery value
    potential_recovery_amount = 0
    for pos_return in returns:
        for line in pos_return.return_lines:
            if line.state == 'resellable':
                potential_recovery_amount += line.subtotal
    
    # Calculate recovery percentage
    recovery_percentage = 0
    if total_refund_amount > 0:
        recovery_percentage = (potential_recovery_amount / total_refund_amount) * 100
    
    # Get monthly returns trend
    monthly_returns = {}
    
    # Get data for the last 6 months
    today = datetime.utcnow()
    for i in range(5, -1, -1):
        month_date = today.replace(day=1) - timedelta(days=i*30)
        month_name = month_date.strftime('%b %Y')
        monthly_returns[month_name] = 0
    
    # Count returns by month
    for pos_return in POSReturn.query.filter(
        POSReturn.return_date >= today.replace(day=1) - timedelta(days=5*30)
    ).all():
        month_name = pos_return.return_date.strftime('%b %Y')
        if month_name in monthly_returns:
            monthly_returns[month_name] += 1
    
    return render_template(
        'pos/returns_report.html',
        returns=returns,
        total_returns=total_returns,
        total_refund_amount=total_refund_amount,
        reason_counts=reason_counts,
        status_counts=status_counts,
        customer_counts=sorted_customers,
        disposition_counts=disposition_counts,
        potential_recovery_amount=potential_recovery_amount,
        recovery_percentage=recovery_percentage,
        monthly_returns=monthly_returns,
        start_date=start_date,
        end_date=end_date,
        status=status
    )

# API endpoints for returns
@pos.route('/api/orders/<int:order_id>')
@login_required
def api_order_detail(order_id):
    """API endpoint to get order details for returns"""
    try:
        order = POSOrder.query.get_or_404(order_id)
        
        # Check if the order has any returnable lines using SQL
        returnable_check_query = """
        SELECT COUNT(*) FROM pos_order_lines
        WHERE order_id = :order_id
        AND quantity > returned_quantity
        """
        
        returnable_count = db.session.execute(
            text(returnable_check_query),
            {'order_id': order_id}
        ).scalar()
        
        if returnable_count == 0:
            return jsonify({
                'success': False,
                'message': 'This order has been fully returned and cannot be returned again.'
            })
        
        # Check if the order already has active returns
        active_returns_query = """
        SELECT COUNT(*) FROM pos_returns
        WHERE original_order_id = :order_id
        AND state IN ('draft', 'validated')
        """
        
        active_returns_count = db.session.execute(
            text(active_returns_query),
            {'order_id': order_id}
        ).scalar()
        
        if active_returns_count > 0:
            return jsonify({
                'success': False,
                'message': 'This order already has an active return. Please complete or cancel the existing return before creating a new one.'
            })
        
        # Get order lines with product details, aggregated by product
        product_totals = {}
        
        for line in order.lines:
            product = Product.query.get(line.product_id)
            if not product:
                continue
                
            returnable_quantity = max(0, line.quantity - line.returned_quantity)
            
            # Only include products that have returnable quantity
            if returnable_quantity > 0:
                if line.product_id not in product_totals:
                    product_totals[line.product_id] = {
                        'product_id': line.product_id,
                        'product_name': product.name,
                        'quantity': 0,
                        'returned_quantity': 0,
                        'returnable_quantity': 0,
                        'unit_price': line.unit_price,
                        'original_lines': []
                    }
                
                # Add this line's quantities to the product total
                product_totals[line.product_id]['quantity'] += line.quantity
                product_totals[line.product_id]['returned_quantity'] += line.returned_quantity
                product_totals[line.product_id]['returnable_quantity'] += returnable_quantity
                
                # Store the original line ID and its returnable quantity for reference
                product_totals[line.product_id]['original_lines'].append({
                    'id': line.id,
                    'returnable_quantity': returnable_quantity
                })
        
        # Convert the product totals dictionary to a list
        lines = list(product_totals.values())
        
        return jsonify({
            'success': True,
            'order': {
                'id': order.id,
                'name': order.name,
                'customer_name': order.customer.name if order.customer else '',
                'customer_phone': order.customer.phone if order.customer else '',
                'order_date': order.order_date.strftime('%Y-%m-%d %H:%M:%S'),
                'total_amount': order.total_amount,
                'lines': lines
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@pos.route('/api/return_products')
@login_required
def api_return_products():
    """API endpoint to get products for returns form"""
    try:
        products = Product.query.filter_by(active=True).all()
        product_list = []
        
        for product in products:
            product_list.append({
                'id': product.id,
                'name': product.name,
                'price': product.sale_price,
                'available_quantity': product.available_quantity
            })
        
        return jsonify(product_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Employee Sales Statistics
@pos.route('/employee-sales')
@login_required
def employee_sales():
    # Check if user has permission to view sales statistics
    if not current_user.has_role('Manager') and not current_user.has_role('Administrator'):
        flash('You do not have permission to view this page.', 'danger')
        return redirect(url_for('pos.index'))
    
    # Get period from query string (default to 'month')
    period = request.args.get('period', 'month')
    
    # Calculate date range based on period
    today = datetime.utcnow().date()
    from_date = None
    
    if period == 'today':
        from_date = today
    elif period == 'week':
        from_date = today - timedelta(days=today.weekday())
    elif period == 'month':
        from_date = today.replace(day=1)
    elif period == 'year':
        from_date = today.replace(month=1, day=1)
    # 'all' will leave from_date as None
    
    # Get all employees who have sales roles
    from modules.employees.models import Employee
    from modules.auth.models import Role
    
    # Get sales worker and manager roles
    sales_roles = Role.query.filter(Role.name.in_(['Sales Worker', 'Manager'])).all()
    sales_role_ids = [role.id for role in sales_roles]
    
    # Get employees with these roles
    employees = []
    for employee in Employee.query.filter_by(is_active=True).all():
        if employee.user and any(role.id in sales_role_ids for role in employee.user.roles):
            employees.append(employee)
    
    # Calculate sales statistics for each employee
    employee_stats = {}
    department_stats = {}
    
    for employee in employees:
        # Query for orders within the date range
        query = POSOrder.query.filter_by(employee_id=employee.id, state='paid')
        
        if from_date:
            query = query.filter(func.date(POSOrder.order_date) >= from_date)
        
        orders = query.all()
        
        # Calculate statistics
        total_sales = sum(order.total_amount for order in orders)
        employee_stats[employee.id] = {
            'orders': len(orders),
            'sales': total_sales
        }
        
        # Add to department statistics if employee has a department
        if employee.department_id:
            dept_id = employee.department_id
            if dept_id not in department_stats:
                department_stats[dept_id] = {
                    'name': employee.department.name,
                    'sales': 0,
                    'orders': 0
                }
            department_stats[dept_id]['sales'] += total_sales
            department_stats[dept_id]['orders'] += len(orders)
    
    # Get POS settings for currency symbol
    pos_settings = POSSettings.query.first()
    currency_symbol = pos_settings.currency_symbol if pos_settings else '₵'
    
    return render_template(
        'pos/employee_sales.html',
        employees=employees,
        employee_stats=employee_stats,
        department_stats=department_stats,
        period=period,
        currency_symbol=currency_symbol
    )

@pos.route('/employee-sales/<int:employee_id>')
@login_required
def employee_sales_detail(employee_id):
    # Check if user has permission to view sales statistics
    if not current_user.has_role('Manager') and not current_user.has_role('Administrator'):
        flash('You do not have permission to view this page.', 'danger')
        return redirect(url_for('pos.index'))
    
    # Get period from query string (default to 'month')
    period = request.args.get('period', 'month')
    
    # Calculate date range based on period
    today = datetime.utcnow().date()
    from_date = None
    
    if period == 'today':
        from_date = today
        time_format = '%H:00'  # Hourly for today
    elif period == 'week':
        from_date = today - timedelta(days=today.weekday())
        time_format = '%a'  # Day of week
    elif period == 'month':
        from_date = today.replace(day=1)
        time_format = '%d'  # Day of month
    elif period == 'year':
        from_date = today.replace(month=1, day=1)
        time_format = '%b'  # Month name
    # 'all' will leave from_date as None
    
    # Get the employee
    from modules.employees.models import Employee
    employee = Employee.query.get_or_404(employee_id)
    
    # Query for orders within the date range
    query = POSOrder.query.filter_by(employee_id=employee_id, state='paid')
    
    if from_date:
        query = query.filter(func.date(POSOrder.order_date) >= from_date)
    
    orders = query.order_by(POSOrder.order_date.desc()).all()
    
    # Calculate overall statistics
    total_sales = sum(order.total_amount for order in orders)
    total_orders = len(orders)
    average_sale = total_sales / total_orders if total_orders > 0 else 0
    
    # Calculate total items sold
    total_items = 0
    for order in orders:
        for line in order.lines:
            total_items += line.quantity
    
    # Get top products
    product_sales = {}
    for order in orders:
        for line in order.lines:
            product_id = line.product_id
            if product_id not in product_sales:
                product_sales[product_id] = {
                    'name': line.product.name,
                    'quantity': 0,
                    'total': 0
                }
            product_sales[product_id]['quantity'] += line.quantity
            product_sales[product_id]['total'] += line.subtotal
    
    # Sort products by total sales and get top 5
    top_products = sorted(
        [product_sales[pid] for pid in product_sales],
        key=lambda x: x['total'],
        reverse=True
    )[:5]
    
    # Calculate payment method statistics
    payment_methods = []
    payment_amounts = []
    payment_stats = {}
    
    for order in orders:
        method = order.payment_method.capitalize()
        if method not in payment_stats:
            payment_stats[method] = 0
        payment_stats[method] += order.total_amount
    
    for method in payment_stats:
        payment_methods.append(method)
        payment_amounts.append(payment_stats[method])
    
    # Prepare time series data for chart
    time_labels = []
    sales_data = []
    
    if period == 'today':
        # Hourly breakdown for today
        hours = {}
        for hour in range(24):
            hours[hour] = 0
        
        for order in orders:
            hour = order.order_date.hour
            hours[hour] += order.total_amount
        
        for hour in range(24):
            time_labels.append(f"{hour}:00")
            sales_data.append(hours[hour])
    
    elif period == 'week':
        # Daily breakdown for week
        days = {}
        for i in range(7):
            day = (from_date + timedelta(days=i))
            days[day.strftime('%a')] = 0
        
        for order in orders:
            day = order.order_date.strftime('%a')
            days[day] += order.total_amount
        
        for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']:
            time_labels.append(day)
            sales_data.append(days[day])
    
    elif period == 'month':
        # Daily breakdown for month
        days = {}
        days_in_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        days_in_month = days_in_month.day
        
        for i in range(1, days_in_month + 1):
            days[i] = 0
        
        for order in orders:
            day = order.order_date.day
            days[day] += order.total_amount
        
        for day in range(1, days_in_month + 1):
            time_labels.append(str(day))
            sales_data.append(days[day])
    
    elif period == 'year':
        # Monthly breakdown for year
        months = {}
        for i in range(1, 13):
            month_name = datetime(2000, i, 1).strftime('%b')
            months[month_name] = 0
        
        for order in orders:
            month = order.order_date.strftime('%b')
            months[month] += order.total_amount
        
        for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']:
            time_labels.append(month)
            sales_data.append(months[month])
    
    else:  # 'all'
        # Monthly breakdown for all time
        months = {}
        
        for order in orders:
            month_year = order.order_date.strftime('%b %Y')
            if month_year not in months:
                months[month_year] = 0
            months[month_year] += order.total_amount
        
        # Sort by date
        sorted_months = sorted(months.keys(), key=lambda x: datetime.strptime(x, '%b %Y'))
        
        for month in sorted_months:
            time_labels.append(month)
            sales_data.append(months[month])
    
    # Get POS settings for currency symbol
    pos_settings = POSSettings.query.first()
    currency_symbol = pos_settings.currency_symbol if pos_settings else '₵'
    
    return render_template(
        'pos/employee_sales_detail.html',
        employee=employee,
        orders=orders[:20],  # Limit to 20 most recent orders
        total_sales=total_sales,
        total_orders=total_orders,
        average_sale=average_sale,
        total_items=total_items,
        top_products=top_products,
        payment_methods=payment_methods,
        payment_amounts=payment_amounts,
        time_labels=time_labels,
        sales_data=sales_data,
        period=period,
        currency_symbol=currency_symbol
    )

@pos.route('/api/customers')
@login_required
def api_customers():
    """API endpoint to get customers for POS terminal"""
    try:
        # Get search term if provided
        search = request.args.get('search', '')
        
        # Base query
        query = Customer.query.filter_by(is_active=True)
        
        # Apply search if provided
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Customer.name.ilike(search_term),
                    Customer.phone.ilike(search_term),
                    Customer.email.ilike(search_term)
                )
            )
        
        # Get customers
        customers = query.order_by(Customer.name).all()
        
        # Add a "Walk-in Customer" option
        result = [{
            'id': None,
            'name': 'Walk-in Customer',
            'phone': '',
            'email': ''
        }]
        
        # Add actual customers
        for customer in customers:
            result.append({
                'id': customer.id,
                'name': customer.name,
                'phone': customer.phone or '',
                'email': customer.email or ''
            })
        
        return jsonify({'success': True, 'customers': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@pos.route('/api/customers/create', methods=['POST'])
@login_required
def api_create_customer():
    """API endpoint to create a new customer from POS terminal"""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'success': False, 'message': 'Customer name is required'})
        
        # Create new customer
        customer = Customer(
            name=data.get('name'),
            phone=data.get('phone', ''),
            email=data.get('email', ''),
            notes=data.get('notes', '')
        )
        
        db.session.add(customer)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Customer created successfully',
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'phone': customer.phone or '',
                'email': customer.email or ''
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})
