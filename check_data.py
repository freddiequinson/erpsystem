from app import create_app
from modules.employees.models import Employee
from modules.pos.models import POSOrder, POSSession

app = create_app()

with app.app_context():
    # Check employees
    print(f'Total employees: {Employee.query.count()}')
    for emp in Employee.query.all():
        print(f'Employee: {emp.first_name} {emp.last_name} (ID: {emp.id})')
    
    # Check POS orders
    print(f'\nTotal POS orders: {POSOrder.query.count()}')
    for order in POSOrder.query.limit(5).all():
        print(f'Order: {order.id}, Employee: {order.employee_id}, Date: {order.order_date}, Amount: {order.total_amount}')
    
    # Check POS sessions
    print(f'\nTotal POS sessions: {POSSession.query.count()}')
    for session in POSSession.query.limit(5).all():
        print(f'Session: {session.id}, Start: {session.start_time}, End: {session.end_time}, State: {session.state}')
        # Check if the session has a user_id attribute instead of employee_id
        if hasattr(session, 'user_id'):
            print(f'  User ID: {session.user_id}')
        # Print all attributes of the session object
        print(f'  Session attributes: {dir(session)}')
