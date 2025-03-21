from datetime import datetime
from app import db

class Category(db.Model):
    __tablename__ = 'product_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(255))
    parent_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'))
    
    parent = db.relationship('Category', remote_side=[id], backref=db.backref('children', lazy='dynamic'))
    products = db.relationship('Product', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<Category {self.name}>'


class UnitOfMeasure(db.Model):
    __tablename__ = 'uom'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    code = db.Column(db.String(10), nullable=False)
    category = db.Column(db.String(64), nullable=False)  # e.g., 'weight', 'length', 'unit'
    ratio = db.Column(db.Float, default=1.0)  # Conversion ratio to reference UOM
    
    products = db.relationship('Product', backref='uom', lazy='dynamic')
    
    def __repr__(self):
        return f'<UOM {self.name}>'


class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    sku = db.Column(db.String(64), unique=True)
    barcode = db.Column(db.String(64), unique=True)
    category_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'))
    uom_id = db.Column(db.Integer, db.ForeignKey('uom.id'))
    product_type = db.Column(db.String(20), default='stockable')  # stockable, consumable, service
    cost_price = db.Column(db.Float, default=0.0)
    sale_price = db.Column(db.Float, default=0.0)
    min_stock = db.Column(db.Float, default=0.0)
    max_stock = db.Column(db.Float, default=0.0)
    weight = db.Column(db.Float, default=0.0)
    volume = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    image_path = db.Column(db.String(255))
    
    stock_moves = db.relationship('StockMove', backref='product', lazy='dynamic')
    
    def __repr__(self):
        return f'<Product {self.name}>'
    
    @property
    def available_quantity(self):
        """Calculate available quantity based on stock moves"""
        from sqlalchemy import func
        from modules.inventory.models import StockMove, StockLocation
        
        # Get internal locations
        internal_locations = StockLocation.query.filter_by(location_type='internal').with_entities(StockLocation.id).all()
        internal_location_ids = [loc.id for loc in internal_locations]
        
        # Calculate quantity from stock moves
        inbound = StockMove.query.filter(
            StockMove.product_id == self.id,
            StockMove.destination_location_id.in_(internal_location_ids),
            StockMove.state == 'done'
        ).with_entities(func.sum(StockMove.quantity)).scalar() or 0
        
        outbound = StockMove.query.filter(
            StockMove.product_id == self.id,
            StockMove.source_location_id.in_(internal_location_ids),
            StockMove.state == 'done'
        ).with_entities(func.sum(StockMove.quantity)).scalar() or 0
        
        return inbound - outbound


class Warehouse(db.Model):
    __tablename__ = 'warehouses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    code = db.Column(db.String(10), nullable=False, unique=True)
    address = db.Column(db.String(255))
    
    locations = db.relationship('StockLocation', backref='warehouse', lazy='dynamic')
    
    def __repr__(self):
        return f'<Warehouse {self.name}>'


class StockLocation(db.Model):
    __tablename__ = 'stock_locations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    code = db.Column(db.String(20), nullable=True)  # Add code field
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'))
    parent_id = db.Column(db.Integer, db.ForeignKey('stock_locations.id'))
    location_type = db.Column(db.String(20), nullable=False)  # internal, customer, supplier, inventory_loss, production
    
    parent = db.relationship('StockLocation', remote_side=[id], backref=db.backref('children', lazy='dynamic'))
    source_moves = db.relationship('StockMove', foreign_keys='StockMove.source_location_id', backref='source_location', lazy='dynamic')
    destination_moves = db.relationship('StockMove', foreign_keys='StockMove.destination_location_id', backref='destination_location', lazy='dynamic')
    
    def __repr__(self):
        return f'<StockLocation {self.name}>'


class StockMove(db.Model):
    __tablename__ = 'stock_moves'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    source_location_id = db.Column(db.Integer, db.ForeignKey('stock_locations.id'), nullable=False)
    destination_location_id = db.Column(db.Integer, db.ForeignKey('stock_locations.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    state = db.Column(db.String(20), default='draft')  # draft, confirmed, done, cancelled
    reference = db.Column(db.String(64))  # Reference to originating document (e.g., PO001, SO001)
    reference_type = db.Column(db.String(20))  # Type of reference (e.g., purchase, sale, inventory)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    scheduled_date = db.Column(db.DateTime)
    effective_date = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<StockMove {self.id}: {self.quantity} units of product {self.product_id}>'


class Inventory(db.Model):
    __tablename__ = 'inventories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('stock_locations.id'), nullable=False)
    state = db.Column(db.String(20), default='draft')  # draft, in_progress, validated, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    validated_at = db.Column(db.DateTime)
    
    location = db.relationship('StockLocation', backref='inventories')
    lines = db.relationship('InventoryLine', backref='inventory', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Inventory {self.name}>'


class InventoryLine(db.Model):
    __tablename__ = 'inventory_lines'
    
    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventories.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    theoretical_qty = db.Column(db.Float, default=0.0)  # Quantity expected based on system
    product_qty = db.Column(db.Float, default=0.0)  # Quantity counted physically
    
    product = db.relationship('Product', backref='inventory_lines')
    
    def __repr__(self):
        return f'<InventoryLine {self.id}: {self.product_qty} units of product {self.product_id}>'
