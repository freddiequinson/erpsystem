from flask import Flask
from flask_migrate import Migrate
from extensions import db
from config import Config
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
migrate = Migrate(app, db)

# Import all models to ensure they're registered with SQLAlchemy
from modules.auth.models import User, Role, UserRole
from modules.inventory.models import Product, Category, StockLocation, StockMove
from modules.pos.models import POSSession, POSCashRegister, POSCategory, POSPaymentMethod, POSDiscount, POSTax, POSReceiptSettings, POSSettings
from modules.sales.models import Customer, SalesOrder, SalesOrderLine

with app.app_context():
    # Create a migration to update the receipt settings table
    from alembic import op
    import sqlalchemy as sa
    
    # Check if the columns already exist
    inspector = sa.inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('pos_receipt_settings')]
    
    # Add columns that don't exist
    if 'logo_path' not in columns:
        op.add_column('pos_receipt_settings', sa.Column('logo_path', sa.String(255), nullable=True))
    
    if 'show_barcode' not in columns:
        op.add_column('pos_receipt_settings', sa.Column('show_barcode', sa.Boolean, default=True))
    
    if 'show_qr_code' not in columns:
        op.add_column('pos_receipt_settings', sa.Column('show_qr_code', sa.Boolean, default=True))
    
    if 'show_customer' not in columns:
        op.add_column('pos_receipt_settings', sa.Column('show_customer', sa.Boolean, default=True))
    
    # Set default values for new boolean columns
    op.execute("UPDATE pos_receipt_settings SET show_barcode = 1, show_qr_code = 1, show_customer = 1")
    
    print("Migration completed successfully!")
