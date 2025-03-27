from app import create_app
from extensions import db
from modules.inventory.models import StockLocation

app = create_app()
with app.app_context():
    locations = StockLocation.query.all()
    print('Stock Locations:')
    for loc in locations:
        print(f"ID: {loc.id}, Name: {loc.name}, Code: {loc.code}, Type: {loc.location_type}")
