from flask import Flask
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extensions import db
from modules.auth.models import Role

app = Flask(__name__)
app.config.from_object('config')
db.init_app(app)

def add_sales_worker_role():
    with app.app_context():
        # Check if Sales Worker role already exists
        sales_worker_role = Role.query.filter_by(name='Sales Worker').first()
        
        if not sales_worker_role:
            # Create Sales Worker role
            sales_worker_role = Role(
                name='Sales Worker',
                description='Sales staff with access limited to POS and returns management'
            )
            db.session.add(sales_worker_role)
            db.session.commit()
            print("Sales Worker role created successfully!")
        else:
            print("Sales Worker role already exists.")

if __name__ == '__main__':
    add_sales_worker_role()
