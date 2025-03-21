from datetime import datetime
from app import db
from modules.inventory.models import Product, StockMove, StockLocation

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    contact_name = db.Column(db.String(64))
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
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    purchase_orders = db.relationship('PurchaseOrder', backref='supplier', lazy='dynamic')
    
    def __repr__(self):
        return f'<Supplier {self.name}>'


class PurchaseOrder(db.Model):
    __tablename__ = 'purchase_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    expected_date = db.Column(db.DateTime)
    state = db.Column(db.String(20), default='draft')  # draft, sent, confirmed, received, cancelled
    total_amount = db.Column(db.Float, default=0.0)
    tax_amount = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='purchase_orders')
    lines = db.relationship('PurchaseOrderLine', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    receipts = db.relationship('PurchaseReceipt', backref='purchase_order', lazy='dynamic')
    
    def __repr__(self):
        return f'<PurchaseOrder {self.name}>'
    
    def calculate_totals(self):
        """Calculate order totals based on lines"""
        self.total_amount = sum(line.subtotal for line in self.lines)
        self.tax_amount = sum(line.tax_amount for line in self.lines)
        return self.total_amount + self.tax_amount
    
    @property
    def total_received_quantity(self):
        """Calculate total received quantity for all lines"""
        return {line.product_id: line.received_quantity for line in self.lines}
    
    @property
    def is_fully_received(self):
        """Check if all products have been received"""
        for line in self.lines:
            if line.received_quantity < line.quantity:
                return False
        return True


class PurchaseOrderLine(db.Model):
    __tablename__ = 'purchase_order_lines'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    description = db.Column(db.String(255))
    quantity = db.Column(db.Float, nullable=False, default=1.0)
    received_quantity = db.Column(db.Float, default=0.0)
    unit_price = db.Column(db.Float, nullable=False, default=0.0)
    tax_percent = db.Column(db.Float, default=0.0)
    expected_date = db.Column(db.DateTime)
    
    product = db.relationship('Product', backref='purchase_order_lines')
    
    @property
    def subtotal(self):
        """Calculate line subtotal"""
        return self.quantity * self.unit_price
    
    @property
    def tax_amount(self):
        """Calculate line tax amount"""
        return self.subtotal * (self.tax_percent / 100)
    
    @property
    def remaining_quantity(self):
        """Calculate remaining quantity to receive"""
        return max(0, self.quantity - self.received_quantity)
    
    def __repr__(self):
        return f'<PurchaseOrderLine {self.id}: {self.quantity} x {self.product_id}>'


class PurchaseReceipt(db.Model):
    __tablename__ = 'purchase_receipts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    receipt_date = db.Column(db.DateTime, default=datetime.utcnow)
    state = db.Column(db.String(20), default='draft')  # draft, done, cancelled
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='purchase_receipts')
    lines = db.relationship('PurchaseReceiptLine', backref='receipt', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<PurchaseReceipt {self.name}>'
    
    def create_stock_moves(self):
        """Create stock moves for the purchase receipt"""
        # Find stock locations
        supplier_location = StockLocation.query.filter_by(location_type='supplier').first()
        stock_location = StockLocation.query.filter_by(location_type='internal', name='Stock').first()
        
        if not supplier_location or not stock_location:
            return False
        
        for line in self.lines:
            stock_move = StockMove(
                product_id=line.product_id,
                source_location_id=supplier_location.id,
                destination_location_id=stock_location.id,
                quantity=line.quantity,
                state='done',
                reference=self.name,
                reference_type='purchase',
                effective_date=self.receipt_date
            )
            db.session.add(stock_move)
            
            # Update the received quantity in the purchase order line
            po_line = PurchaseOrderLine.query.filter_by(
                order_id=self.purchase_order_id, 
                product_id=line.product_id
            ).first()
            
            if po_line:
                po_line.received_quantity += line.quantity
        
        # Check if the purchase order is fully received
        purchase_order = self.purchase_order
        if purchase_order.is_fully_received:
            purchase_order.state = 'received'
        
        return True


class PurchaseReceiptLine(db.Model):
    __tablename__ = 'purchase_receipt_lines'
    
    id = db.Column(db.Integer, primary_key=True)
    receipt_id = db.Column(db.Integer, db.ForeignKey('purchase_receipts.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    description = db.Column(db.String(255))
    quantity = db.Column(db.Float, nullable=False, default=1.0)
    
    product = db.relationship('Product', backref='purchase_receipt_lines')
    
    def __repr__(self):
        return f'<PurchaseReceiptLine {self.id}: {self.quantity} x {self.product_id}>'


class PurchaseInvoice(db.Model):
    __tablename__ = 'purchase_invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'))
    invoice_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    state = db.Column(db.String(20), default='draft')  # draft, validated, paid, cancelled
    total_amount = db.Column(db.Float, default=0.0)
    tax_amount = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    supplier = db.relationship('Supplier', backref='purchase_invoices')
    purchase_order = db.relationship('PurchaseOrder', backref='invoices')
    user = db.relationship('User', backref='purchase_invoices')
    lines = db.relationship('PurchaseInvoiceLine', backref='invoice', lazy='dynamic', cascade='all, delete-orphan')
    payments = db.relationship('PurchasePayment', backref='invoice', lazy='dynamic')
    
    def __repr__(self):
        return f'<PurchaseInvoice {self.name}>'
    
    def calculate_totals(self):
        """Calculate invoice totals based on lines"""
        self.total_amount = sum(line.subtotal for line in self.lines)
        self.tax_amount = sum(line.tax_amount for line in self.lines)
        return self.total_amount + self.tax_amount
    
    @property
    def amount_paid(self):
        """Calculate total amount paid"""
        return sum(payment.amount for payment in self.payments)
    
    @property
    def amount_due(self):
        """Calculate remaining amount due"""
        return (self.total_amount + self.tax_amount) - self.amount_paid


class PurchaseInvoiceLine(db.Model):
    __tablename__ = 'purchase_invoice_lines'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('purchase_invoices.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    description = db.Column(db.String(255))
    quantity = db.Column(db.Float, nullable=False, default=1.0)
    unit_price = db.Column(db.Float, nullable=False, default=0.0)
    tax_percent = db.Column(db.Float, default=0.0)
    
    product = db.relationship('Product', backref='purchase_invoice_lines')
    
    @property
    def subtotal(self):
        """Calculate line subtotal"""
        return self.quantity * self.unit_price
    
    @property
    def tax_amount(self):
        """Calculate line tax amount"""
        return self.subtotal * (self.tax_percent / 100)
    
    def __repr__(self):
        return f'<PurchaseInvoiceLine {self.id}: {self.quantity} x {self.product_id}>'


class PurchasePayment(db.Model):
    __tablename__ = 'purchase_payments'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('purchase_invoices.id'), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20))  # cash, bank_transfer, check, other
    reference = db.Column(db.String(64))
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='purchase_payments')
    
    def __repr__(self):
        return f'<PurchasePayment {self.id}: {self.amount}>'
