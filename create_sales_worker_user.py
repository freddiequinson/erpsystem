from flask import Flask
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extensions import db
from modules.auth.models import Role, User, UserRole

app = Flask(__name__)
app.config.from_object('config')
db.init_app(app)

def create_sales_worker_user():
    """Create a new user with the Sales Worker role"""
    with app.app_context():
        # Check if Sales Worker role exists
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
        
        # Check if user already exists
        username = "salesuser"
        existing_user = User.query.filter_by(username=username).first()
        
        if existing_user:
            print(f"User '{username}' already exists.")
            
            # Check if user already has the Sales Worker role
            if existing_user.has_role('Sales Worker'):
                print(f"User '{username}' already has the Sales Worker role.")
            else:
                # Assign the Sales Worker role to the user
                user_role = UserRole(user_id=existing_user.id, role_id=sales_worker_role.id)
                db.session.add(user_role)
                db.session.commit()
                print(f"Sales Worker role assigned to user '{username}'.")
            
            print(f"Login credentials: Username: {username}, Password: password123")
            return
        
        # Create new user
        new_user = User(
            username=username,
            email="salesuser@example.com",
            first_name="Sales",
            last_name="User",
            is_active=True
        )
        new_user.set_password("password123")
        db.session.add(new_user)
        db.session.commit()
        
        # Assign the Sales Worker role to the user
        user_role = UserRole(user_id=new_user.id, role_id=sales_worker_role.id)
        db.session.add(user_role)
        db.session.commit()
        
        print(f"Sales Worker user created successfully!")
        print(f"Login credentials: Username: {username}, Password: password123")

if __name__ == '__main__':
    create_sales_worker_user()
