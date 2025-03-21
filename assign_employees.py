from app import create_app
from modules.employees.models import Employee
from modules.pos.models import POSOrder, POSSession
from modules.auth.models import User
import random

app = create_app()

with app.app_context():
    # Get all employees
    employees = Employee.query.all()
    if not employees:
        print("No employees found in the database.")
        exit()
    
    # Get all orders without an employee assigned
    orders = POSOrder.query.filter_by(employee_id=None).all()
    print(f"Found {len(orders)} orders without an employee assigned.")
    
    # Assign employees to orders
    for order in orders:
        # Randomly select an employee
        employee = random.choice(employees)
        order.employee_id = employee.id
    
    # Commit the changes
    from app import db
    db.session.commit()
    
    print(f"Successfully assigned employees to {len(orders)} orders.")
    
    # Verify the changes
    for emp in employees:
        order_count = POSOrder.query.filter_by(employee_id=emp.id).count()
        print(f"Employee {emp.first_name} {emp.last_name} now has {order_count} orders assigned.")
