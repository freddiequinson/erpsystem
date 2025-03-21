import os
from app import create_app
from extensions import db
from modules.pos.models import POSReceiptSettings

# Create application context
app = create_app(os.getenv('FLASK_CONFIG') or 'default')
with app.app_context():
    # Create the pos_receipt_settings table
    db.create_all()
    
    # Check if there's already a receipt settings record
    settings = POSReceiptSettings.query.first()
    
    # If not, create default settings
    if not settings:
        settings = POSReceiptSettings(
            header_text="Thank you for shopping with us!",
            footer_text="Please come again!",
            show_logo=True,
            show_cashier=True,
            show_tax_details=True
        )
        db.session.add(settings)
        db.session.commit()
        print("Receipt settings table created and default settings added.")
    else:
        print("Receipt settings table already exists.")
