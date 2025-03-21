import os
from app import create_app
from extensions import db
from flask_migrate import Migrate, upgrade

# Create application context
app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)

with app.app_context():
    # Import all models to ensure they're registered with SQLAlchemy
    from modules.pos.models import POSReceiptSettings
    
    # Create a migration for the database
    print("Creating database tables...")
    db.create_all()
    
    # Check if there's already a receipt settings record
    settings = None
    try:
        settings = POSReceiptSettings.query.first()
    except Exception as e:
        print(f"Error checking for existing settings: {e}")
    
    # If not, create default settings
    if not settings:
        try:
            settings = POSReceiptSettings(
                header_text="Thank you for shopping with us!",
                footer_text="Please come again!",
                show_logo=True,
                show_cashier=True,
                show_tax_details=True
            )
            db.session.add(settings)
            db.session.commit()
            print("Default receipt settings added.")
        except Exception as e:
            print(f"Error adding default settings: {e}")
            db.session.rollback()
    else:
        print("Receipt settings already exist.")
