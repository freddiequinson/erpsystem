from app import create_app, db
from modules.purchase.models import PurchaseOrder, Supplier

app = create_app()
with app.app_context():
    print("Purchase Orders:")
    orders = PurchaseOrder.query.all()
    for order in orders:
        print(f"ID: {order.id}, Name: {order.name}, State: {order.state}")
    
    print("\nSuppliers:")
    suppliers = Supplier.query.all()
    for supplier in suppliers:
        print(f"ID: {supplier.id}, Name: {supplier.name}")
