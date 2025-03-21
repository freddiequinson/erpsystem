from datetime import datetime
from app import db
from modules.inventory.models import Product, StockMove, StockLocation

class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(255))
    city = db.Column(db.String(64))
    state = db.Column(db.String(64))
    zip_code = db.Column(db.String(20))
    country = db.Column(db.String(64))
    website = db.Column(db.String(120))
    tax_id = db.Column(db.String(64))
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    sales_orders = db.relationship('SalesOrder', backref='customer', lazy='dynamic')
    
    def __repr__(self):
        return f'<Customer {self.name}>'


class SalesOrder(db.Model):
    __tablename__ = 'sales_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    expected_date = db.Column(db.DateTime)
    state = db.Column(db.String(20), default='draft')  # draft, confirmed, done, cancelled
    total_amount = db.Column(db.Float, default=0.0)
    tax_amount = db.Column(db.Float, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    lines = db.relationship('SalesOrderLine', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    invoices = db.relationship('Invoice', backref='sales_order', lazy='dynamic')
    
    def __repr__(self):
        return f'<SalesOrder {self.name}>'
    
    def calculate_totals(self):
        """Calculate order totals based on lines"""
        self.total_amount = sum(line.subtotal for line in self.lines)
        self.tax_amount = sum(line.tax_amount for line in self.lines)
        return self.total_amount + self.tax_amount - self.discount_amount
    
    def create_stock_moves(self):
        """Create stock moves for the sales order"""
        # Find stock locations
        stock_location = StockLocation.query.filter_by(location_type='internal', name='Stock').first()
        customer_location = StockLocation.query.filter_by(location_type='customer').first()
        
        if not stock_location or not customer_location:
            return False
        
        for line in self.lines:
            stock_move = StockMove(
                product_id=line.product_id,
                source_location_id=stock_location.id,
                destination_location_id=customer_location.id,
                quantity=line.quantity,
                state='draft',
                reference=self.name,
                reference_type='sale',
                scheduled_date=self.expected_date
            )
            db.session.add(stock_move)
        
        return True


class SalesOrderLine(db.Model):
    __tablename__ = 'sales_order_lines'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('sales_orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    description = db.Column(db.String(255))
    quantity = db.Column(db.Float, nullable=False, default=1.0)
    unit_price = db.Column(db.Float, nullable=False, default=0.0)
    discount_percent = db.Column(db.Float, default=0.0)
    tax_percent = db.Column(db.Float, default=0.0)
    
    product = db.relationship('Product', backref='sales_order_lines')
    
    @property
    def subtotal(self):
        """Calculate line subtotal"""
        return self.quantity * self.unit_price * (1 - self.discount_percent / 100)
    
    @property
    def tax_amount(self):
        """Calculate line tax amount"""
        return self.subtotal * (self.tax_percent / 100)
    
    def __repr__(self):
        return f'<SalesOrderLine {self.id}: {self.quantity} x {self.product_id}>'


class Invoice(db.Model):
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    sales_order_id = db.Column(db.Integer, db.ForeignKey('sales_orders.id'))
    invoice_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    state = db.Column(db.String(20), default='draft')  # draft, open, paid, cancelled
    total_amount = db.Column(db.Float, default=0.0)
    tax_amount = db.Column(db.Float, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    customer = db.relationship('Customer', backref='invoices')
    lines = db.relationship('InvoiceLine', backref='invoice', lazy='dynamic', cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='invoice', lazy='dynamic')
    
    def __repr__(self):
        return f'<Invoice {self.name}>'
    
    def calculate_totals(self):
        """Calculate invoice totals based on lines"""
        self.total_amount = sum(line.subtotal for line in self.lines)
        self.tax_amount = sum(line.tax_amount for line in self.lines)
        return self.total_amount + self.tax_amount - self.discount_amount
    
    @property
    def amount_due(self):
        """Calculate amount due"""
        paid_amount = sum(payment.amount for payment in self.payments if payment.state == 'posted')
        return self.calculate_totals() - paid_amount


class InvoiceLine(db.Model):
    __tablename__ = 'invoice_lines'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    description = db.Column(db.String(255))
    quantity = db.Column(db.Float, nullable=False, default=1.0)
    unit_price = db.Column(db.Float, nullable=False, default=0.0)
    discount_percent = db.Column(db.Float, default=0.0)
    tax_percent = db.Column(db.Float, default=0.0)
    
    product = db.relationship('Product', backref='invoice_lines')
    
    @property
    def subtotal(self):
        """Calculate line subtotal"""
        return self.quantity * self.unit_price * (1 - self.discount_percent / 100)
    
    @property
    def tax_amount(self):
        """Calculate line tax amount"""
        return self.subtotal * (self.tax_percent / 100)
    
    def __repr__(self):
        return f'<InvoiceLine {self.id}: {self.quantity} x {self.product_id}>'


class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    amount = db.Column(db.Float, nullable=False, default=0.0)
    payment_method = db.Column(db.String(64))
    reference = db.Column(db.String(64))
    state = db.Column(db.String(20), default='draft')  # draft, posted, cancelled
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Payment {self.name}>'
