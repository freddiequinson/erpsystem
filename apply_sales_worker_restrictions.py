from flask import Flask
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extensions import db
from modules.auth.models import Role, User, UserRole
from modules.auth.decorators import sales_worker_forbidden

app = Flask(__name__)
app.config.from_object('config')
db.init_app(app)

def create_sales_worker_role():
    """Create the Sales Worker role if it doesn't exist"""
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
            return sales_worker_role
        else:
            print("Sales Worker role already exists.")
            return sales_worker_role

def assign_sales_worker_role_to_user(username):
    """Assign the Sales Worker role to a specific user"""
    with app.app_context():
        # Get the user
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"User '{username}' not found.")
            return False
        
        # Get the Sales Worker role
        sales_worker_role = Role.query.filter_by(name='Sales Worker').first()
        if not sales_worker_role:
            print("Sales Worker role not found. Creating it...")
            sales_worker_role = create_sales_worker_role()
        
        # Check if user already has the role
        if user.has_role('Sales Worker'):
            print(f"User '{username}' already has the Sales Worker role.")
            return True
        
        # Assign the role to the user
        user_role = UserRole(user_id=user.id, role_id=sales_worker_role.id)
        db.session.add(user_role)
        db.session.commit()
        print(f"Sales Worker role assigned to user '{username}' successfully!")
        return True

def list_users():
    """List all users and their roles"""
    with app.app_context():
        users = User.query.all()
        print("\nUsers and their roles:")
        print("-----------------------")
        for user in users:
            roles = [role.name for role in user.roles]
            print(f"Username: {user.username}, Roles: {', '.join(roles) if roles else 'No roles'}")

if __name__ == '__main__':
    # Create the Sales Worker role
    create_sales_worker_role()
    
    # List all users
    list_users()
    
    # Ask if user wants to assign the Sales Worker role to a user
    print("\nDo you want to assign the Sales Worker role to a user? (y/n)")
    choice = input().lower()
    
    if choice == 'y':
        print("Enter the username:")
        username = input()
        assign_sales_worker_role_to_user(username)
        
        # Show updated user list
        list_users()
