from flask import Flask
from extensions import db
from modules.inventory.models import StockLocation
from modules.auth.models import Branch

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///odoo_clone.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    print("\n=== BRANCHES FROM SQLALCHEMY ===")
    branches = Branch.query.all()
    for branch in branches:
        print(f"ID: {branch.id}, Name: {branch.name}")
    
    print("\n=== STOCK LOCATIONS FROM SQLALCHEMY ===")
    locations = StockLocation.query.all()
    for loc in locations:
        branch_name = "No Branch"
        if loc.branch_id:
            branch = Branch.query.get(loc.branch_id)
            if branch:
                branch_name = branch.name
        
        print(f"ID: {loc.id}, Name: {loc.name}, Type: {loc.location_type}, Branch ID: {loc.branch_id}, Branch: {branch_name}")
