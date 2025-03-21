from app import create_app
from modules.employees.models import Employee
from modules.pos.models import POSOrder, POSSession
from modules.auth.models import User

app = create_app()

with app.app_context():
    # Check employees
    print(f'Total employees: {Employee.query.count()}')
    for emp in Employee.query.all():
        print(f'Employee: {emp.first_name} {emp.last_name} (ID: {emp.id})')
        # Check if employee has a user account
        if emp.user_id:
            user = User.query.get(emp.user_id)
            if user:
                print(f'  Associated User: {user.username} (ID: {user.id})')
            else:
                print(f'  User ID {emp.user_id} not found')
        else:
            print(f'  No associated user account')
    
    # Check POS orders
    print(f'\nTotal POS orders: {POSOrder.query.count()}')
    for order in POSOrder.query.all():
        print(f'Order: {order.id}, Employee: {order.employee_id}, Date: {order.order_date}, Amount: {order.total_amount}, State: {order.state}')
    
    # Check if there are any orders without employee_id
    orders_without_employee = POSOrder.query.filter_by(employee_id=None).count()
    print(f'\nOrders without employee_id: {orders_without_employee}')
    
    # Check POS sessions
    print(f'\nTotal POS sessions: {POSSession.query.count()}')
    for session in POSSession.query.all():
        print(f'Session: {session.id}, User: {session.user_id}, Start: {session.start_time}, End: {session.end_time}, State: {session.state}')
