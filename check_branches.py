import os
import sys

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from modules.database import db
from modules.auth.models import Branch
from modules.inventory.models import StockLocation

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///odoo_clone.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    # Check branches
    print("\n=== BRANCHES ===")
    branches = Branch.query.all()
    if branches:
        for branch in branches:
            print(f"ID: {branch.id}, Name: {branch.name}, Active: {branch.is_active}")
    else:
        print("No branches found in the database.")
    
    # Check locations
    print("\n=== STOCK LOCATIONS ===")
    locations = StockLocation.query.all()
    if locations:
        for loc in locations:
            branch_name = "No Branch"
            if loc.branch_id:
                branch = Branch.query.get(loc.branch_id)
                if branch:
                    branch_name = branch.name
            
            print(f"ID: {loc.id}, Name: {loc.name}, Type: {loc.location_type}, Branch ID: {loc.branch_id}, Branch: {branch_name}")
    else:
        print("No stock locations found in the database.")
