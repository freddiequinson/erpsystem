from app import create_app, db
from modules.pos.models import POSOrder
from modules.employees.models import Employee
from flask_login import current_user
from sqlalchemy import text

def check_pos_orders():
    """Check the POS orders and their employee associations"""
    
    app = create_app()
    with app.app_context():
        # Check all orders
        orders = POSOrder.query.all()
        print(f"Total orders in database: {len(orders)}")
        
        # Check orders with employee_id set
        orders_with_employee = POSOrder.query.filter(POSOrder.employee_id.isnot(None)).all()
        print(f"Orders with employee_id set: {len(orders_with_employee)}")
        
        # Print details of each order
        print("\nOrder details:")
        for order in orders:
            print(f"Order ID: {order.id}, Name: {order.name}, Employee ID: {order.employee_id}")
        
        # Check all employees
        employees = Employee.query.all()
        print(f"\nTotal employees in database: {len(employees)}")
        
        # Print details of each employee
        print("\nEmployee details:")
        for employee in employees:
            print(f"Employee ID: {employee.id}, Name: {employee.full_name}, User ID: {employee.user_id}")
            
        # Check if there are any orders with employee_id that match existing employees
        if employees and orders:
            employee_ids = [emp.id for emp in employees]
            matching_orders = POSOrder.query.filter(POSOrder.employee_id.in_(employee_ids)).all()
            print(f"\nOrders with valid employee_id: {len(matching_orders)}")
            
            # Print details of matching orders
            print("\nMatching order details:")
            for order in matching_orders:
                employee = Employee.query.get(order.employee_id)
                print(f"Order ID: {order.id}, Name: {order.name}, Employee: {employee.full_name if employee else 'Unknown'}")

if __name__ == "__main__":
    check_pos_orders()
