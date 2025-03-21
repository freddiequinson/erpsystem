import os
from app import create_app
from extensions import db
from modules.sales.models import Customer, SalesOrder, SalesOrderLine, Invoice, InvoiceLine, Payment
from modules.inventory.models import Product, StockLocation, StockMove
from datetime import datetime, timedelta
import random

def create_sample_data():
    # Create the Flask app
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    
    with app.app_context():
        print("Creating sample sales data...")
        
        # Check if we already have customers
        if Customer.query.count() > 0:
            print("Customers already exist, skipping customer creation.")
        else:
            # Create sample customers
            customers = [
                Customer(
                    name="Kwame Enterprises",
                    email="info@kwameenterprises.com",
                    phone="+233 20 123 4567",
                    address="15 Independence Ave",
                    city="Accra",
                    state="Greater Accra",
                    zip_code="00233",
                    country="Ghana",
                    is_active=True
                ),
                Customer(
                    name="Abena Retail Ltd",
                    email="sales@abenaretail.com",
                    phone="+233 24 987 6543",
                    address="25 Liberation Road",
                    city="Kumasi",
                    state="Ashanti",
                    zip_code="00234",
                    country="Ghana",
                    is_active=True
                ),
                Customer(
                    name="Kofi Trading Co.",
                    email="contact@kofitrading.com",
                    phone="+233 27 456 7890",
                    address="5 Harbor Road",
                    city="Takoradi",
                    state="Western",
                    zip_code="00235",
                    country="Ghana",
                    is_active=True
                ),
                Customer(
                    name="Akua Stores",
                    email="info@akuastores.com",
                    phone="+233 26 789 0123",
                    address="10 Market Street",
                    city="Tamale",
                    state="Northern",
                    zip_code="00236",
                    country="Ghana",
                    is_active=True
                ),
                Customer(
                    name="Yaw Distributors",
                    email="sales@yawdistributors.com",
                    phone="+233 23 345 6789",
                    address="30 Main Road",
                    city="Cape Coast",
                    state="Central",
                    zip_code="00237",
                    country="Ghana",
                    is_active=True
                )
            ]
            
            for customer in customers:
                db.session.add(customer)
            
            db.session.commit()
            print(f"Created {len(customers)} sample customers.")
        
        # Get products
        products = Product.query.filter_by(is_active=True).all()
        
        if not products:
            print("No active products found. Please create products first.")
            return
        
        # Get customers
        customers = Customer.query.filter_by(is_active=True).all()
        
        if not customers:
            print("No active customers found. Please create customers first.")
            return
        
        # Check if we already have sales orders
        if SalesOrder.query.count() > 0:
            print("Sales orders already exist, skipping order creation.")
        else:
            # Create sample sales orders
            for i in range(10):
                # Generate order date within the last 60 days
                days_ago = random.randint(0, 60)
                order_date = datetime.now() - timedelta(days=days_ago)
                
                # Select a random customer
                customer = random.choice(customers)
                
                # Generate order name
                order_number = i + 1
                order_name = f"SO{order_number:04d}"
                
                # Create the order
                order = SalesOrder(
                    name=order_name,
                    customer_id=customer.id,
                    order_date=order_date,
                    expected_date=order_date + timedelta(days=7),
                    state='draft',
                    notes=f"Sample order for {customer.name}",
                    created_at=order_date
                )
                
                db.session.add(order)
                db.session.commit()
                
                # Add 1-5 random products to the order
                num_products = random.randint(1, 5)
                selected_products = random.sample(products, min(num_products, len(products)))
                
                for product in selected_products:
                    quantity = random.randint(1, 10)
                    unit_price = product.sale_price
                    
                    line = SalesOrderLine(
                        order_id=order.id,
                        product_id=product.id,
                        description=product.name,
                        quantity=quantity,
                        unit_price=unit_price,
                        tax_rate=0  # No tax for simplicity
                    )
                    
                    # Calculate line totals
                    line.subtotal = line.quantity * line.unit_price
                    line.tax_amount = line.subtotal * (line.tax_rate / 100)
                    
                    db.session.add(line)
                
                db.session.commit()
                
                # Calculate order totals
                order.calculate_totals()
                
                # Randomly set some orders to confirmed or done state
                if i % 3 == 0:  # Every 3rd order stays as draft
                    pass
                elif i % 3 == 1:  # Every 3rd+1 order is confirmed
                    # Find stock locations
                    stock_location = StockLocation.query.filter_by(location_type='internal', name='Stock').first()
                    customer_location = StockLocation.query.filter_by(location_type='customer').first()
                    
                    if stock_location and customer_location:
                        order.state = 'confirmed'
                        
                        # Create stock moves
                        for line in order.lines:
                            move = StockMove(
                                product_id=line.product_id,
                                source_location_id=stock_location.id,
                                destination_location_id=customer_location.id,
                                quantity=line.quantity,
                                state='draft',
                                reference=order.name,
                                reference_type='sale'
                            )
                            db.session.add(move)
                    else:
                        print(f"Warning: Could not confirm order {order.name} due to missing stock locations.")
                else:  # Every 3rd+2 order is done
                    stock_location = StockLocation.query.filter_by(location_type='internal', name='Stock').first()
                    customer_location = StockLocation.query.filter_by(location_type='customer').first()
                    
                    if stock_location and customer_location:
                        order.state = 'done'
                        
                        # Create stock moves
                        for line in order.lines:
                            move = StockMove(
                                product_id=line.product_id,
                                source_location_id=stock_location.id,
                                destination_location_id=customer_location.id,
                                quantity=line.quantity,
                                state='done',
                                reference=order.name,
                                reference_type='sale'
                            )
                            db.session.add(move)
                    else:
                        print(f"Warning: Could not complete order {order.name} due to missing stock locations.")
                
                db.session.commit()
            
            print(f"Created 10 sample sales orders with product lines.")
        
        # Check if we already have invoices
        if Invoice.query.count() > 0:
            print("Invoices already exist, skipping invoice creation.")
        else:
            # Create invoices for confirmed and done orders
            orders = SalesOrder.query.filter(SalesOrder.state.in_(['confirmed', 'done'])).all()
            
            for order in orders:
                # Generate invoice name
                invoice_number = Invoice.query.count() + 1
                invoice_name = f"INV{invoice_number:04d}"
                
                # Create invoice
                invoice = Invoice(
                    name=invoice_name,
                    customer_id=order.customer_id,
                    order_id=order.id,
                    invoice_date=order.order_date + timedelta(days=1),
                    due_date=order.order_date + timedelta(days=15),
                    state='draft',
                    notes=f"Invoice for order {order.name}"
                )
                
                db.session.add(invoice)
                db.session.commit()
                
                # Copy order lines to invoice lines
                for order_line in order.lines:
                    invoice_line = InvoiceLine(
                        invoice_id=invoice.id,
                        product_id=order_line.product_id,
                        description=order_line.description,
                        quantity=order_line.quantity,
                        unit_price=order_line.unit_price,
                        tax_rate=order_line.tax_rate
                    )
                    
                    # Calculate line totals
                    invoice_line.subtotal = invoice_line.quantity * invoice_line.unit_price
                    invoice_line.tax_amount = invoice_line.subtotal * (invoice_line.tax_rate / 100)
                    
                    db.session.add(invoice_line)
                
                db.session.commit()
                
                # Calculate invoice totals
                invoice.calculate_totals()
                
                # Validate some invoices
                if random.choice([True, False]):
                    invoice.state = 'open'
                    
                    # Create payments for some open invoices
                    if random.choice([True, False]):
                        payment_date = invoice.invoice_date + timedelta(days=random.randint(1, 10))
                        
                        # Decide if full or partial payment
                        if random.choice([True, False]):
                            # Full payment
                            amount = invoice.total_amount
                            payment = Payment(
                                invoice_id=invoice.id,
                                payment_date=payment_date,
                                amount=amount,
                                payment_method='cash',
                                reference=f"PAY-{invoice.name}",
                                notes=f"Full payment for invoice {invoice.name}"
                            )
                            db.session.add(payment)
                            
                            # Update invoice state
                            invoice.state = 'paid'
                        else:
                            # Partial payment (50-90% of total)
                            percentage = random.uniform(0.5, 0.9)
                            amount = invoice.total_amount * percentage
                            payment = Payment(
                                invoice_id=invoice.id,
                                payment_date=payment_date,
                                amount=amount,
                                payment_method='bank_transfer',
                                reference=f"PAY-{invoice.name}-PART",
                                notes=f"Partial payment for invoice {invoice.name}"
                            )
                            db.session.add(payment)
                
                db.session.commit()
            
            print(f"Created invoices for {len(orders)} orders with payment records.")
        
        print("Sample data creation completed.")

if __name__ == "__main__":
    create_sample_data()
