from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from modules.inventory.models import Product, StockMove, StockLocation

class POSSession(db.Model):
    __tablename__ = 'pos_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    state = db.Column(db.String(20), default='open')  # open, closed, cancelled
    opening_balance = db.Column(db.Float, default=0.0)
    closing_balance = db.Column(db.Float)
    cash_register_id = db.Column(db.Integer, db.ForeignKey('pos_cash_registers.id'))
    notes = db.Column(db.Text)
    
    user = db.relationship('User', backref='pos_sessions')
    cash_register = db.relationship('POSCashRegister', backref='sessions')
    orders = db.relationship('POSOrder', backref='session', lazy='dynamic')
    
    def __repr__(self):
        return f'<POSSession {self.name}>'
    
    @property
    def total_sales(self):
        """Calculate total sales for the session"""
        return sum(order.total_amount for order in self.orders if order.state == 'paid')
    
    @property
    def cash_sales(self):
        """Calculate cash sales for the session"""
        return sum(order.total_amount for order in self.orders if order.state == 'paid' and order.payment_method == 'cash')
    
    @property
    def card_sales(self):
        """Calculate card sales for the session"""
        return sum(order.total_amount for order in self.orders if order.state == 'paid' and order.payment_method == 'card')
    
    @property
    def other_sales(self):
        """Calculate other payment method sales for the session"""
        return sum(order.total_amount for order in self.orders if order.state == 'paid' and order.payment_method not in ['cash', 'card'])


class POSCashRegister(db.Model):
    __tablename__ = 'pos_cash_registers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    
    def __repr__(self):
        return f'<POSCashRegister {self.name}>'


class POSOrder(db.Model):
    __tablename__ = 'pos_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('pos_sessions.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    employee = db.relationship('Employee', backref='pos_orders')
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    state = db.Column(db.String(20), default='draft')  # draft, paid, cancelled, refunded
    total_amount = db.Column(db.Float, default=0.0)
    tax_amount = db.Column(db.Float, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    payment_method = db.Column(db.String(20))
    payment_reference = db.Column(db.String(64))
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Use string references instead of direct class references
    customer = db.relationship('Customer', backref='pos_orders')
    user = db.relationship('User', backref='pos_orders')
    lines = db.relationship('POSOrderLine', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    returns = db.relationship('POSReturn', foreign_keys='POSReturn.original_order_id', back_populates='original_order')
    
    def __repr__(self):
        return f'<POSOrder {self.name}>'
    
    @property
    def is_fully_returned(self):
        """Check if all order lines have been fully returned"""
        # If there are no lines, the order can't be fully returned
        if not self.lines.count():
            print(f"Order {self.name} has no lines, not fully returned")
            return False
        
        # Check if any line has returnable quantity
        all_fully_returned = True
        for line in self.lines:
            # Calculate returnable quantity directly to avoid any caching issues
            returnable_qty = max(0, line.quantity - line.returned_quantity)
            
            # Debug information
            print(f"Order {self.name}, Line {line.id}: quantity={line.quantity}, returned={line.returned_quantity}, returnable={returnable_qty}")
            
            if returnable_qty > 0:
                print(f"Order {self.name}, Line {line.id} has returnable quantity {returnable_qty}, not fully returned")
                all_fully_returned = False
        
        if all_fully_returned:
            print(f"Order {self.name} is fully returned, all lines have zero returnable quantity")
        
        return all_fully_returned
    
    def has_active_returns(self):
        """Check if this order has any active returns (draft or validated)"""
        from sqlalchemy import or_
        active_returns = POSReturn.query.filter(
            POSReturn.original_order_id == self.id,
            or_(POSReturn.state == 'draft', POSReturn.state == 'validated')
        ).count()
        return active_returns > 0
    
    def calculate_totals(self):
        """Calculate order totals based on lines"""
        self.total_amount = sum(line.subtotal for line in self.lines)
        self.tax_amount = sum(line.tax_amount for line in self.lines)
        return self.total_amount + self.tax_amount - self.discount_amount
    
    def create_stock_moves(self):
        """Create stock moves for the POS order"""
        # Find stock locations
        stock_location = StockLocation.query.filter_by(location_type='internal', code='SHOP').first()
        customer_location = StockLocation.query.filter_by(location_type='customer').first()
        
        if not stock_location or not customer_location:
            return False
        
        for line in self.lines:
            product = Product.query.get(line.product_id)
            if not product:
                raise ValueError(f"Product {line.product_id} not found")
            
            if product.product_type == 'service':
                continue
            
            if product.available_quantity < line.quantity:
                raise ValueError(f"Insufficient quantity of product {product.name} available")
            
            stock_move = StockMove(
                product_id=line.product_id,
                source_location_id=stock_location.id,
                destination_location_id=customer_location.id,
                quantity=line.quantity,
                state='done',  # POS orders create done stock moves immediately
                reference=self.name,
                reference_type='pos',
                effective_date=self.order_date
            )
            db.session.add(stock_move)
        
        db.session.commit()
        return True


class POSOrderLine(db.Model):
    __tablename__ = 'pos_order_lines'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('pos_orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    description = db.Column(db.String(255))
    quantity = db.Column(db.Float, nullable=False, default=1.0)
    unit_price = db.Column(db.Float, nullable=False, default=0.0)
    discount_percent = db.Column(db.Float, default=0.0)
    tax_percent = db.Column(db.Float, default=0.0)
    returned_quantity = db.Column(db.Float, default=0.0)
    
    product = db.relationship('Product', backref='pos_order_lines')
    return_lines = db.relationship('POSReturnLine', back_populates='original_order_line')
    
    @property
    def returnable_quantity(self):
        """Calculate how much quantity can still be returned"""
        # Ensure we're using the most up-to-date values
        db.session.refresh(self)
        
        # Calculate and return the returnable quantity
        returnable = max(0, self.quantity - self.returned_quantity)
        print(f"Calculated returnable quantity for line {self.id}: {returnable} (quantity: {self.quantity}, returned: {self.returned_quantity})")
        return returnable
    
    @property
    def subtotal(self):
        """Calculate line subtotal"""
        return self.quantity * self.unit_price * (1 - self.discount_percent / 100)
    
    @property
    def tax_amount(self):
        """Calculate line tax amount"""
        return self.subtotal * (self.tax_percent / 100)
    
    def __repr__(self):
        return f'<POSOrderLine {self.id}: {self.quantity} x {self.product_id}>'


class POSCategory(db.Model):
    __tablename__ = 'pos_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('pos_categories.id'))
    sequence = db.Column(db.Integer, default=10)
    image_path = db.Column(db.String(255))
    
    parent = db.relationship('POSCategory', remote_side=[id], backref=db.backref('children', lazy='dynamic'))
    
    def __repr__(self):
        return f'<POSCategory {self.name}>'


class POSPaymentMethod(db.Model):
    __tablename__ = 'pos_payment_methods'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    is_cash = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<POSPaymentMethod {self.name}>'


class POSDiscount(db.Model):
    __tablename__ = 'pos_discounts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    discount_type = db.Column(db.String(20), nullable=False)  # 'percentage' or 'fixed'
    value = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<POSDiscount {self.name}>'


class POSTax(db.Model):
    __tablename__ = 'pos_taxes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    rate = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<POSTax {self.name}>'


class POSReceiptSettings(db.Model):
    __tablename__ = 'pos_receipt_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    header_text = db.Column(db.String(255))
    footer_text = db.Column(db.String(255))
    company_name = db.Column(db.String(255))
    company_address = db.Column(db.String(255))
    company_phone = db.Column(db.String(255))
    logo_path = db.Column(db.String(255))
    show_logo = db.Column(db.Boolean, default=True)
    show_cashier = db.Column(db.Boolean, default=True)
    show_tax_details = db.Column(db.Boolean, default=True)
    show_barcode = db.Column(db.Boolean, default=True)
    show_qr_code = db.Column(db.Boolean, default=True)
    show_customer = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<POSReceiptSettings {self.id}>'


class POSSettings(db.Model):
    __tablename__ = 'pos_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    currency_symbol = db.Column(db.String(10), default="₵")
    default_customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    allow_negative_stock = db.Column(db.Boolean, default=False)
    restrict_price_edit = db.Column(db.Boolean, default=True)
    auto_print_receipt = db.Column(db.Boolean, default=True)
    
    # Use string references instead of direct class references
    default_customer = db.relationship('Customer', foreign_keys=[default_customer_id])
    
    def __repr__(self):
        return f'<POSSettings {self.id}>'


class POSReturn(db.Model):
    __tablename__ = 'pos_returns'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    original_order_id = db.Column(db.Integer, db.ForeignKey('pos_orders.id'))
    customer_name = db.Column(db.String(128))
    customer_phone = db.Column(db.String(64))
    return_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, default=0.0)
    refund_amount = db.Column(db.Float, default=0.0)
    return_type = db.Column(db.String(20))  # full, partial
    refund_method = db.Column(db.String(20))  # cash, card, store_credit, exchange
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    state = db.Column(db.String(20), default='draft')  # draft, validated, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    original_order = db.relationship('POSOrder', foreign_keys=[original_order_id], back_populates='returns')
    return_lines = db.relationship('POSReturnLine', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<POSReturn {self.name}>'
    
    def generate_name(self):
        """Generate a unique return reference"""
        if not self.name:
            last_return = POSReturn.query.order_by(POSReturn.id.desc()).first()
            last_id = last_return.id if last_return else 0
            self.name = f'RET{str(last_id + 1).zfill(4)}'
        return self.name
    
    def validate_return(self):
        """Validate the return and process refund/exchange"""
        if self.state != 'draft':
            return False
            
        # Create stock moves for returned products
        self.create_stock_moves()
        
        # Update returned quantities on original order lines
        for return_line in self.return_lines:
            if return_line.original_order_line:
                # Update the returned quantity on the original order line
                return_line.original_order_line.returned_quantity += return_line.quantity
                # Update the return line state to pending for quality checks
                return_line.state = 'pending'
        
        # Commit changes to ensure returned_quantity is updated in the database
        db.session.commit()
                
        # Update state
        self.state = 'validated'
        
        # Calculate the total refund amount if not already set
        if not self.refund_amount or self.refund_amount <= 0:
            self.refund_amount = sum(line.subtotal for line in self.return_lines)
            
        # Set the return date to now if not already set
        if not self.return_date:
            self.return_date = datetime.utcnow()
            
        # Make sure refund method is set
        if not self.refund_method and self.original_order:
            self.refund_method = self.original_order.payment_method
        
        db.session.commit()
        
        # Print debug information
        print(f"Return {self.name} validated successfully")
        print(f"Refund amount: {self.refund_amount}")
        print(f"Refund method: {self.refund_method}")
        print(f"Return date: {self.return_date}")
        
        if self.original_order:
            print(f"Original order: {self.original_order.name}, is_fully_returned: {self.original_order.is_fully_returned}")
            for line in self.original_order.lines:
                print(f"  Line {line.id}: quantity = {line.quantity}, returned_quantity = {line.returned_quantity}, returnable_quantity = {line.returnable_quantity}")
        
        return True
    
    def create_stock_moves(self):
        """Create stock moves for returned products"""
        from modules.inventory.models import StockMove, StockLocation
        
        # Get stock locations
        shop_location = StockLocation.query.filter_by(code='SHOP').first()
        customer_location = StockLocation.query.filter_by(location_type='customer').first()
        quality_location = StockLocation.query.filter_by(code='QC').first()
        
        # If quality control location doesn't exist, create it
        if not quality_location:
            quality_location = StockLocation(
                name='Quality Control',
                code='QC',
                location_type='internal',
                warehouse_id=shop_location.warehouse_id if shop_location else None
            )
            db.session.add(quality_location)
            db.session.commit()
        
        # Create stock moves for each return line
        for line in self.return_lines:
            if line.product.product_type == 'service':
                continue
                
            # Move from customer to quality control
            stock_move = StockMove(
                product_id=line.product_id,
                source_location_id=customer_location.id if customer_location else None,
                destination_location_id=quality_location.id,
                quantity=line.quantity,
                reference=f"Return {self.name}",
                state='done'
            )
            db.session.add(stock_move)
        
        db.session.commit()


class POSReturnLine(db.Model):
    __tablename__ = 'pos_return_lines'
    
    id = db.Column(db.Integer, primary_key=True)
    return_id = db.Column(db.Integer, db.ForeignKey('pos_returns.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    original_order_line_id = db.Column(db.Integer, db.ForeignKey('pos_order_lines.id'), nullable=True)
    quantity = db.Column(db.Float, default=0.0)
    unit_price = db.Column(db.Float, default=0.0)
    subtotal = db.Column(db.Float, default=0.0)
    return_reason = db.Column(db.String(64))
    state = db.Column(db.String(20), default='draft')
    
    # Relationships
    product = db.relationship('Product')
    pos_return = db.relationship('POSReturn', foreign_keys=[return_id])
    original_order_line = db.relationship('POSOrderLine', foreign_keys=[original_order_line_id], back_populates='return_lines')
    
    def __repr__(self):
        return f'<POSReturnLine {self.id}>'


class QualityCheck(db.Model):
    __tablename__ = 'quality_checks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    return_line_id = db.Column(db.Integer, db.ForeignKey('pos_return_lines.id'), nullable=False)
    quality_state = db.Column(db.String(20), default='pending')
    disposition = db.Column(db.String(20))
    quantity = db.Column(db.Float, default=0.0)  # New field to track partial quantities
    notes = db.Column(db.Text)
    checked_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    check_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    return_line = db.relationship('POSReturnLine', backref=db.backref('quality_check', uselist=False))
    checked_by_user = db.relationship('User', foreign_keys=[checked_by])
    
    def __repr__(self):
        return f'<QualityCheck {self.id}>'
    
    def process_result(self):
        """Process the quality check result and move product to appropriate location"""
        # Handle partial quantities by splitting the return line if needed
        return_line = self.return_line
        
        # Check if return_line exists
        if not return_line:
            raise ValueError("Cannot process quality check: Return line not found")
            
        processed_quantity = self.quantity
        
        # If processing less than the full quantity, split the return line
        if processed_quantity < return_line.quantity:
            # Create a new return line for the remaining quantity
            remaining_quantity = return_line.quantity - processed_quantity
            
            # Update the original return line quantity to match the processed quantity
            return_line.quantity = processed_quantity
            
            # Create a new return line for the remaining quantity
            new_line = POSReturnLine(
                return_id=return_line.return_id,
                product_id=return_line.product_id,
                quantity=remaining_quantity,
                unit_price=return_line.unit_price,
                subtotal=return_line.unit_price * remaining_quantity,
                return_reason=return_line.return_reason,
                state='pending'  # Keep the remaining quantity as pending
            )
            db.session.add(new_line)
            db.session.commit()
        
        # Update return line status based on quality check result
        if self.quality_state == 'pass' or self.quality_state == 'not_defective':
            return_line.state = 'resellable'
        else:
            return_line.state = 'defective'
        
        db.session.commit()
        
        # Get necessary stock locations
        shop_location = StockLocation.query.filter_by(name='Shop Floor').first()
        quality_location = StockLocation.query.filter_by(name='Quality Control').first()
        scrap_location = StockLocation.query.filter_by(name='Scrap').first()
        vendor_location = StockLocation.query.filter_by(name='Vendor Returns').first()
        repair_location = StockLocation.query.filter_by(name='Repair Center').first()
        discount_location = StockLocation.query.filter_by(name='Discount Sales').first()
        
        # Determine destination location based on disposition
        destination_location = None
        if self.disposition == 'stock':
            destination_location = shop_location
        elif self.disposition == 'scrap':
            destination_location = scrap_location
        elif self.disposition == 'vendor':
            destination_location = vendor_location
        elif self.disposition == 'repair':
            destination_location = repair_location
        elif self.disposition == 'discount_sale':
            destination_location = discount_location
        else:
            destination_location = shop_location  # Default to shop if unknown
        
        # Create stock move
        if destination_location:
            # Use the quality check quantity instead of the full return line quantity
            move_quantity = self.quantity or return_line.quantity
            
            stock_move = StockMove(
                product_id=self.return_line.product_id,
                source_location_id=quality_location.id if quality_location else None,
                destination_location_id=destination_location.id,
                quantity=move_quantity,
                reference=f"Quality Check {self.id}: {self.quality_state} - {self.disposition} ({move_quantity} units)",
                state='draft'
            )
            db.session.add(stock_move)
            db.session.commit()
            
            # Validate the stock move
            stock_move.state = 'done'  # Use 'done' state to ensure it's counted in available_quantity
            db.session.commit()
            
            # Refresh the product to update available quantity
            product = Product.query.get(self.return_line.product_id)
            if product:
                db.session.refresh(product)
