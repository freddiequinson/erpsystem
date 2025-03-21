from app import create_app
from extensions import db
from modules.auth.models import User, Role, UserRole
from flask import Flask

# Create the Flask application
app = create_app()

def create_sales_user():
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
        
        # Create a new user with login credentials
        username = "salesuser"
        password = "sales123"
        
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        
        if existing_user:
            print(f"User '{username}' already exists.")
            
            # Check if user already has the Sales Worker role
            if any(role.name == 'Sales Worker' for role in existing_user.roles):
                print(f"User '{username}' already has the Sales Worker role.")
            else:
                # Assign the Sales Worker role to the user
                user_role = UserRole(user_id=existing_user.id, role_id=sales_worker_role.id)
                db.session.add(user_role)
                db.session.commit()
                print(f"Sales Worker role assigned to user '{username}'.")
        else:
            # Create new user
            new_user = User(
                username=username,
                email="salesuser@example.com",
                first_name="Sales",
                last_name="User",
                is_active=True
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            
            # Assign the Sales Worker role to the user
            user_role = UserRole(user_id=new_user.id, role_id=sales_worker_role.id)
            db.session.add(user_role)
            db.session.commit()
            
            print(f"Sales Worker user created successfully!")
        
        print(f"\nLogin credentials:")
        print(f"Username: {username}")
        print(f"Password: {password}")

if __name__ == "__main__":
    create_sales_user()
