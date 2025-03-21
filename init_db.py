import os
import sys
from datetime import datetime, date, timedelta
import bcrypt
from app import create_app, db
from modules.auth.models import User, Role, UserRole
from modules.inventory.models import Category, UnitOfMeasure, Product, Warehouse, StockLocation, StockMove, Inventory, InventoryLine
from modules.sales.models import Customer, SalesOrder, SalesOrderLine, Invoice, InvoiceLine, Payment
from modules.pos.models import POSSession, POSCashRegister, POSOrder, POSOrderLine, POSCategory, POSPaymentMethod
from modules.purchase.models import Supplier, PurchaseOrder, PurchaseOrderLine, PurchaseReceipt, PurchaseReceiptLine, PurchaseInvoice, PurchaseInvoiceLine, PurchasePayment
from modules.employees.models import Department, JobPosition, Employee, LeaveType, LeaveAllocation, Attendance

def init_db():
    app = create_app('development')
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if database is already initialized
        if User.query.first() is not None:
            print("Database already initialized!")
            return
        
        # Create roles
        admin_role = Role(name='Admin', description='Administrator with full access')
        manager_role = Role(name='Manager', description='Manager with elevated access')
        employee_role = Role(name='Employee', description='Regular employee access')
        cashier_role = Role(name='Cashier', description='POS cashier access')
        inventory_role = Role(name='Inventory', description='Inventory management access')
        purchase_role = Role(name='Purchase', description='Purchase management access')
        sales_role = Role(name='Sales', description='Sales management access')
        
        db.session.add_all([admin_role, manager_role, employee_role, cashier_role, inventory_role, purchase_role, sales_role])
        db.session.commit()
        
        # Create admin user
        hashed_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        admin_user = User(
            username='admin',
            email='admin@example.com',
            password_hash=hashed_password,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        # Create manager user
        manager_password = bcrypt.hashpw('manager123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        manager_user = User(
            username='manager',
            email='manager@example.com',
            password_hash=manager_password,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        # Create employee user
        employee_password = bcrypt.hashpw('employee123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        employee_user = User(
            username='employee',
            email='employee@example.com',
            password_hash=employee_password,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        # Create cashier user
        cashier_password = bcrypt.hashpw('cashier123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cashier_user = User(
            username='cashier',
            email='cashier@example.com',
            password_hash=cashier_password,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        db.session.add_all([admin_user, manager_user, employee_user, cashier_user])
        db.session.commit()
        
        # Assign roles to users
        admin_user_role = UserRole(user_id=admin_user.id, role_id=admin_role.id)
        manager_user_role = UserRole(user_id=manager_user.id, role_id=manager_role.id)
        employee_user_role = UserRole(user_id=employee_user.id, role_id=employee_role.id)
        cashier_user_role = UserRole(user_id=cashier_user.id, role_id=cashier_role.id)
        
        db.session.add_all([admin_user_role, manager_user_role, employee_user_role, cashier_user_role])
        
        # Create default product categories
        categories = [
            Category(name='Raw Materials', description='Materials used in manufacturing'),
            Category(name='Finished Goods', description='Completed products ready for sale'),
            Category(name='Services', description='Service products'),
            Category(name='Consumables', description='Items consumed during operations'),
            Category(name='Electronics', description='Electronic products'),
            Category(name='Furniture', description='Furniture products'),
            Category(name='Office Supplies', description='Office supplies and stationery')
        ]
        db.session.add_all(categories)
        db.session.commit()
        
        # Create units of measure
        units = [
            UnitOfMeasure(name='Units', code='UNT', category='unit', ratio=1.0),
            UnitOfMeasure(name='Kilograms', code='KG', category='weight', ratio=1.0),
            UnitOfMeasure(name='Liters', code='L', category='volume', ratio=1.0),
            UnitOfMeasure(name='Meters', code='M', category='length', ratio=1.0),
            UnitOfMeasure(name='Boxes', code='BOX', category='unit', ratio=12.0),
            UnitOfMeasure(name='Pairs', code='PR', category='unit', ratio=2.0)
        ]
        db.session.add_all(units)
        db.session.commit()
        
        # Create sample products
        products = [
            Product(name='Laptop', description='High-performance laptop', category_id=5, uom_id=1, 
                   cost_price=800.00, sale_price=1200.00, barcode='1234567890123', is_active=True),
            Product(name='Office Chair', description='Ergonomic office chair', category_id=6, uom_id=1, 
                   cost_price=150.00, sale_price=250.00, barcode='2345678901234', is_active=True),
            Product(name='Desk', description='Office desk', category_id=6, uom_id=1, 
                   cost_price=200.00, sale_price=350.00, barcode='3456789012345', is_active=True),
            Product(name='Notebook', description='100-page notebook', category_id=7, uom_id=1, 
                   cost_price=2.50, sale_price=5.00, barcode='4567890123456', is_active=True),
            Product(name='Pen Set', description='Set of 10 pens', category_id=7, uom_id=5, 
                   cost_price=5.00, sale_price=10.00, barcode='5678901234567', is_active=True)
        ]
        db.session.add_all(products)
        
        # Create default warehouses and locations
        main_warehouse = Warehouse(name='Main Warehouse', code='WH-MAIN', address='123 Main St')
        secondary_warehouse = Warehouse(name='Secondary Warehouse', code='WH-SEC', address='456 Second St')
        db.session.add_all([main_warehouse, secondary_warehouse])
        db.session.commit()
        
        # Create stock locations
        stock_locations = [
            StockLocation(name='Stock', warehouse_id=main_warehouse.id, location_type='internal'),
            StockLocation(name='Input', warehouse_id=main_warehouse.id, location_type='input'),
            StockLocation(name='Output', warehouse_id=main_warehouse.id, location_type='output'),
            StockLocation(name='Quality Control', warehouse_id=main_warehouse.id, location_type='internal'),
            StockLocation(name='Scrap', warehouse_id=main_warehouse.id, location_type='inventory_loss'),
            StockLocation(name='Stock', warehouse_id=secondary_warehouse.id, location_type='internal'),
            StockLocation(name='Input', warehouse_id=secondary_warehouse.id, location_type='input'),
            StockLocation(name='Output', warehouse_id=secondary_warehouse.id, location_type='output'),
            StockLocation(name='Customer', location_type='customer'),
            StockLocation(name='Supplier', location_type='supplier')
        ]
        db.session.add_all(stock_locations)
        db.session.commit()
        
        # Create initial inventory for products
        stock_location = StockLocation.query.filter_by(name='Stock', warehouse_id=main_warehouse.id).first()
        supplier_location = StockLocation.query.filter_by(name='Supplier').first()
        
        # Create stock moves to initialize inventory
        for product in products:
            initial_qty = 10  # Initial quantity for each product
            stock_move = StockMove(
                product_id=product.id,
                source_location_id=supplier_location.id,
                destination_location_id=stock_location.id,
                quantity=initial_qty,
                state='done',
                reference='Initial Inventory',
                reference_type='inventory',
                effective_date=datetime.utcnow()
            )
            db.session.add(stock_move)
        
        # Create departments
        departments = [
            Department(name='Management', code='MGMT'),
            Department(name='Sales', code='SALES'),
            Department(name='Purchasing', code='PURCH'),
            Department(name='Warehouse', code='WH'),
            Department(name='Accounting', code='ACC'),
            Department(name='Human Resources', code='HR'),
            Department(name='IT', code='IT')
        ]
        db.session.add_all(departments)
        db.session.commit()
        
        # Create job positions
        positions = [
            JobPosition(name='CEO', department_id=1),
            JobPosition(name='Sales Manager', department_id=2),
            JobPosition(name='Sales Representative', department_id=2),
            JobPosition(name='Purchasing Manager', department_id=3),
            JobPosition(name='Warehouse Manager', department_id=4),
            JobPosition(name='Accountant', department_id=5),
            JobPosition(name='HR Manager', department_id=6),
            JobPosition(name='IT Manager', department_id=7),
            JobPosition(name='Cashier', department_id=2)
        ]
        db.session.add_all(positions)
        db.session.commit()
        
        # Create employees
        employees = [
            Employee(
                user_id=admin_user.id,
                first_name='Admin',
                last_name='User',
                gender='male',
                hire_date=date.today() - timedelta(days=365),
                department_id=1,
                job_position_id=1,
                work_email='admin@example.com',
                work_phone='555-1111',
                is_active=True
            ),
            Employee(
                user_id=manager_user.id,
                first_name='Manager',
                last_name='User',
                gender='female',
                hire_date=date.today() - timedelta(days=180),
                department_id=2,
                job_position_id=2,
                work_email='manager@example.com',
                work_phone='555-2222',
                is_active=True
            ),
            Employee(
                user_id=employee_user.id,
                first_name='Employee',
                last_name='User',
                gender='male',
                hire_date=date.today() - timedelta(days=90),
                department_id=3,
                job_position_id=4,
                work_email='employee@example.com',
                work_phone='555-3333',
                is_active=True
            ),
            Employee(
                user_id=cashier_user.id,
                first_name='Cashier',
                last_name='User',
                gender='female',
                hire_date=date.today() - timedelta(days=30),
                department_id=2,
                job_position_id=9,
                work_email='cashier@example.com',
                work_phone='555-4444',
                is_active=True
            )
        ]
        db.session.add_all(employees)
        
        # Create leave types
        leave_types = [
            LeaveType(name='Annual Leave', code='AL', max_days=20, is_paid=True),
            LeaveType(name='Sick Leave', code='SL', max_days=10, is_paid=True),
            LeaveType(name='Unpaid Leave', code='UL', max_days=0, is_paid=False),
            LeaveType(name='Maternity Leave', code='ML', max_days=90, is_paid=True),
            LeaveType(name='Paternity Leave', code='PL', max_days=5, is_paid=True)
        ]
        db.session.add_all(leave_types)
        
        # Create leave allocations for employees
        for employee in employees:
            # Annual leave allocation
            annual_leave = LeaveAllocation(
                employee_id=employee.id,
                leave_type_id=1,  # Annual Leave
                allocation_date=date.today(),
                expiry_date=date(date.today().year, 12, 31),
                days_allocated=20.0,
                days_taken=0.0
            )
            
            # Sick leave allocation
            sick_leave = LeaveAllocation(
                employee_id=employee.id,
                leave_type_id=2,  # Sick Leave
                allocation_date=date.today(),
                expiry_date=date(date.today().year, 12, 31),
                days_allocated=10.0,
                days_taken=0.0
            )
            
            db.session.add_all([annual_leave, sick_leave])
        
        # Create sample customers
        customers = [
            Customer(name='ABC Corporation', email='contact@abc.com', phone='555-1234', address='456 Business Ave', city='Business City', state='BS', country='USA', is_active=True),
            Customer(name='XYZ Industries', email='info@xyz.com', phone='555-5678', address='789 Industry Blvd', city='Industry City', state='IN', country='USA', is_active=True),
            Customer(name='123 Retail', email='sales@123retail.com', phone='555-9012', address='101 Retail St', city='Retail City', state='RT', country='USA', is_active=True),
            Customer(name='Tech Solutions', email='info@techsolutions.com', phone='555-3456', address='202 Tech Ave', city='Tech City', state='TC', country='USA', is_active=True)
        ]
        db.session.add_all(customers)
        
        # Create sample suppliers
        suppliers = [
            Supplier(name='Acme Supplies', email='sales@acme.com', phone='555-9876', address='321 Supplier St', city='Supplier City', state='SP', country='USA', is_active=True),
            Supplier(name='Global Materials', email='orders@global.com', phone='555-6543', address='654 Material Rd', city='Material City', state='MT', country='USA', is_active=True),
            Supplier(name='Tech Components', email='sales@techcomp.com', phone='555-7890', address='987 Component Ave', city='Component City', state='CP', country='USA', is_active=True),
            Supplier(name='Office Depot', email='orders@officedepot.com', phone='555-0123', address='246 Office St', city='Office City', state='OF', country='USA', is_active=True)
        ]
        db.session.add_all(suppliers)
        
        # Create POS categories
        pos_categories = [
            POSCategory(name='Electronics', sequence=10),
            POSCategory(name='Furniture', sequence=20),
            POSCategory(name='Office Supplies', sequence=30)
        ]
        db.session.add_all(pos_categories)
        
        # Create POS payment methods
        pos_payment_methods = [
            POSPaymentMethod(name='Cash', code='cash', is_cash=True, is_active=True),
            POSPaymentMethod(name='Credit Card', code='card', is_cash=False, is_active=True),
            POSPaymentMethod(name='Debit Card', code='debit', is_cash=False, is_active=True),
            POSPaymentMethod(name='Check', code='check', is_cash=False, is_active=True)
        ]
        db.session.add_all(pos_payment_methods)
        
        # Create POS cash registers
        pos_cash_registers = [
            POSCashRegister(name='Main Register', balance=1000.00),
            POSCashRegister(name='Secondary Register', balance=500.00)
        ]
        db.session.add_all(pos_cash_registers)
        
        # Commit all changes
        db.session.commit()
        
        print("Database initialized successfully!")

if __name__ == '__main__':
    init_db()
