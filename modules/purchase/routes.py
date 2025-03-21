from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from modules.purchase.models import (
    Supplier, PurchaseOrder, PurchaseOrderLine, 
    PurchaseReceipt, PurchaseReceiptLine,
    PurchaseInvoice, PurchaseInvoiceLine, PurchasePayment
)
from modules.purchase.forms import (
    SupplierForm, PurchaseOrderForm, PurchaseReceiptForm, 
    PurchaseInvoiceForm, PurchasePaymentForm
)
from modules.inventory.models import Product, StockMove, StockLocation
from datetime import datetime

purchase = Blueprint('purchase', __name__, url_prefix='/purchase')

# Suppliers
@purchase.route('/suppliers')
@login_required
def suppliers():
    suppliers = Supplier.query.order_by(Supplier.name).all()
    return render_template('purchase/suppliers.html', suppliers=suppliers)

@purchase.route('/suppliers/new', methods=['GET', 'POST'])
@login_required
def new_supplier():
    form = SupplierForm()
    
    if form.validate_on_submit():
        supplier = Supplier(
            name=form.name.data,
            contact_name=form.contact_name.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            city=form.city.data,
            state=form.state.data,
            zip_code=form.zip_code.data,
            country=form.country.data,
            website=form.website.data,
            tax_id=form.tax_id.data,
            notes=form.notes.data,
            is_active=form.is_active.data
        )
        
        db.session.add(supplier)
        db.session.commit()
        
        flash('Supplier created successfully!', 'success')
        return redirect(url_for('purchase.suppliers'))
    
    return render_template('purchase/supplier_form.html', form=form)

@purchase.route('/suppliers/<int:supplier_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    form = SupplierForm(obj=supplier)
    
    if form.validate_on_submit():
        form.populate_obj(supplier)
        db.session.commit()
        
        flash('Supplier updated successfully!', 'success')
        return redirect(url_for('purchase.view_supplier', supplier_id=supplier.id))
    
    return render_template('purchase/supplier_form.html', form=form, supplier=supplier)

@purchase.route('/suppliers/<int:supplier_id>')
@login_required
def view_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    return render_template('purchase/view_supplier.html', supplier=supplier)

@purchase.route('/suppliers/<int:supplier_id>/delete', methods=['POST'])
@login_required
def delete_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    
    # Check if supplier has purchase orders
    if supplier.purchase_orders.count() > 0:
        flash('Cannot delete supplier with associated purchase orders.', 'danger')
        return redirect(url_for('purchase.view_supplier', supplier_id=supplier.id))
    
    db.session.delete(supplier)
    db.session.commit()
    
    flash('Supplier deleted successfully!', 'success')
    return redirect(url_for('purchase.suppliers'))

# Purchase Orders
@purchase.route('/orders')
@login_required
def orders():
    orders = PurchaseOrder.query.order_by(PurchaseOrder.order_date.desc()).all()
    return render_template('purchase/orders.html', orders=orders)

@purchase.route('/orders/new', methods=['GET', 'POST'])
@login_required
def new_order():
    form = PurchaseOrderForm()
    
    # Populate supplier choices
    suppliers = Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
    form.supplier_id.choices = [(s.id, s.name) for s in suppliers]
    
    # Pre-select supplier if provided in query params
    if request.args.get('supplier_id'):
        form.supplier_id.data = int(request.args.get('supplier_id'))
    
    if form.validate_on_submit():
        # Generate order number (e.g., PO00001)
        last_order = PurchaseOrder.query.order_by(PurchaseOrder.id.desc()).first()
        order_number = f"PO{(last_order.id + 1 if last_order else 1):05d}"
        
        order = PurchaseOrder(
            name=order_number,
            supplier_id=form.supplier_id.data,
            order_date=form.order_date.data,
            expected_date=form.expected_date.data,
            notes=form.notes.data,
            state='draft',
            user_id=current_user.id
        )
        
        db.session.add(order)
        db.session.commit()
        
        flash('Purchase order created successfully!', 'success')
        return redirect(url_for('purchase.edit_order_lines', order_id=order.id))
    
    # Get all products for the order lines
    products = Product.query.order_by(Product.name).all()
    
    return render_template('purchase/create_order.html', form=form, products=products)

@purchase.route('/orders/<int:order_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_order(order_id):
    order = PurchaseOrder.query.get_or_404(order_id)
    
    # Only draft orders can be edited
    if order.state != 'draft':
        flash('Only draft orders can be edited.', 'warning')
        return redirect(url_for('purchase.view_order', order_id=order.id))
    
    form = PurchaseOrderForm(obj=order)
    
    # Populate supplier choices
    suppliers = Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
    form.supplier_id.choices = [(s.id, s.name) for s in suppliers]
    
    if form.validate_on_submit():
        form.populate_obj(order)
        db.session.commit()
        
        flash('Purchase order updated successfully!', 'success')
        return redirect(url_for('purchase.view_order', order_id=order.id))
    
    return render_template('purchase/create_order.html', form=form, order=order)

@purchase.route('/orders/<int:order_id>')
@login_required
def view_order(order_id):
    order = PurchaseOrder.query.get_or_404(order_id)
    return render_template('purchase/view_order.html', order=order)

@purchase.route('/orders/<int:order_id>/lines', methods=['GET', 'POST'])
@login_required
def edit_order_lines(order_id):
    order = PurchaseOrder.query.get_or_404(order_id)
    
    # Only draft orders can be edited
    if order.state != 'draft':
        flash('Only draft orders can be edited.', 'warning')
        return redirect(url_for('purchase.view_order', order_id=order.id))
    
    # Get all products for the order lines
    products = Product.query.order_by(Product.name).all()
    
    return render_template('purchase/create_order.html', order=order, products=products)

@purchase.route('/orders/<int:order_id>/confirm', methods=['GET', 'POST'])
@login_required
def confirm_order(order_id):
    order = PurchaseOrder.query.get_or_404(order_id)
    
    # Check if order has lines
    if order.lines.count() == 0:
        flash('Cannot confirm an order without any products.', 'danger')
        return redirect(url_for('purchase.view_order', order_id=order.id))
    
    # Only draft orders can be confirmed
    if order.state != 'draft':
        flash('Only draft orders can be confirmed.', 'warning')
        return redirect(url_for('purchase.view_order', order_id=order.id))
    
    # Update order state
    order.state = 'confirmed'
    order.confirmation_date = datetime.utcnow()
    db.session.commit()
    
    flash('Purchase order confirmed successfully!', 'success')
    return redirect(url_for('purchase.view_order', order_id=order.id))

@purchase.route('/orders/<int:order_id>/cancel', methods=['GET', 'POST'])
@login_required
def cancel_order(order_id):
    order = PurchaseOrder.query.get_or_404(order_id)
    
    # Only draft or confirmed orders can be cancelled
    if order.state not in ['draft', 'confirmed']:
        flash('This order cannot be cancelled.', 'warning')
        return redirect(url_for('purchase.view_order', order_id=order.id))
    
    # Update order state
    order.state = 'cancelled'
    db.session.commit()
    
    flash('Purchase order cancelled successfully!', 'success')
    return redirect(url_for('purchase.view_order', order_id=order.id))

@purchase.route('/orders/<int:order_id>/delete', methods=['POST'])
@login_required
def delete_order(order_id):
    order = PurchaseOrder.query.get_or_404(order_id)
    
    # Only draft orders can be deleted
    if order.state != 'draft':
        flash('Only draft orders can be deleted.', 'danger')
        return redirect(url_for('purchase.view_order', order_id=order.id))
    
    # Delete order lines first
    for line in order.lines:
        db.session.delete(line)
    
    db.session.delete(order)
    db.session.commit()
    
    flash('Purchase order deleted successfully!', 'success')
    return redirect(url_for('purchase.orders'))

# API endpoints for purchase order lines
@purchase.route('/api/orders/<int:order_id>/lines', methods=['GET'])
@login_required
def api_get_order_lines(order_id):
    order = PurchaseOrder.query.get_or_404(order_id)
    lines = []
    
    for line in order.lines:
        lines.append({
            'id': line.id,
            'product_id': line.product_id,
            'product_name': line.product.name,
            'product_sku': line.product.sku,
            'quantity': line.quantity,
            'unit_price': line.unit_price,
            'tax_rate': line.tax_rate,
            'subtotal': line.subtotal,
            'tax_amount': line.tax_amount,
            'received_quantity': line.received_quantity,
            'invoiced_quantity': line.invoiced_quantity
        })
    
    return jsonify({'lines': lines})

@purchase.route('/api/orders/<int:order_id>/lines', methods=['POST'])
@login_required
def api_add_order_line(order_id):
    order = PurchaseOrder.query.get_or_404(order_id)
    
    # Only draft orders can be edited
    if order.state != 'draft':
        return jsonify({'success': False, 'message': 'Only draft orders can be edited'}), 400
    
    data = request.json
    
    if not data or 'product_id' not in data:
        return jsonify({'success': False, 'message': 'Product ID is required'}), 400
    
    product = Product.query.get(data['product_id'])
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404
    
    # Check if line with this product already exists
    existing_line = PurchaseOrderLine.query.filter_by(
        purchase_order_id=order.id, 
        product_id=product.id
    ).first()
    
    if existing_line:
        # Update existing line
        existing_line.quantity += float(data.get('quantity', 1))
        existing_line.unit_price = float(data.get('unit_price', product.purchase_price or 0))
        existing_line.tax_rate = float(data.get('tax_rate', 0))
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Line updated successfully',
            'line': {
                'id': existing_line.id,
                'product_id': existing_line.product_id,
                'product_name': product.name,
                'product_sku': product.sku,
                'quantity': existing_line.quantity,
                'unit_price': existing_line.unit_price,
                'tax_rate': existing_line.tax_rate,
                'subtotal': existing_line.subtotal,
                'tax_amount': existing_line.tax_amount
            }
        })
    else:
        # Create new line
        line = PurchaseOrderLine(
            purchase_order_id=order.id,
            product_id=product.id,
            quantity=float(data.get('quantity', 1)),
            unit_price=float(data.get('unit_price', product.purchase_price or 0)),
            tax_rate=float(data.get('tax_rate', 0))
        )
        
        db.session.add(line)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Line added successfully',
            'line': {
                'id': line.id,
                'product_id': line.product_id,
                'product_name': product.name,
                'product_sku': product.sku,
                'quantity': line.quantity,
                'unit_price': line.unit_price,
                'tax_rate': line.tax_rate,
                'subtotal': line.subtotal,
                'tax_amount': line.tax_amount
            }
        })

@purchase.route('/api/lines/<int:line_id>', methods=['PUT'])
@login_required
def api_update_order_line(line_id):
    line = PurchaseOrderLine.query.get_or_404(line_id)
    
    # Only draft orders can be edited
    if line.purchase_order.state != 'draft':
        return jsonify({'success': False, 'message': 'Only draft orders can be edited'}), 400
    
    data = request.json
    
    if 'quantity' in data:
        line.quantity = float(data['quantity'])
    
    if 'unit_price' in data:
        line.unit_price = float(data['unit_price'])
    
    if 'tax_rate' in data:
        line.tax_rate = float(data['tax_rate'])
    
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': 'Line updated successfully',
        'line': {
            'id': line.id,
            'quantity': line.quantity,
            'unit_price': line.unit_price,
            'tax_rate': line.tax_rate,
            'subtotal': line.subtotal,
            'tax_amount': line.tax_amount
        }
    })

@purchase.route('/api/lines/<int:line_id>', methods=['DELETE'])
@login_required
def api_delete_order_line(line_id):
    line = PurchaseOrderLine.query.get_or_404(line_id)
    
    # Only draft orders can be edited
    if line.purchase_order.state != 'draft':
        return jsonify({'success': False, 'message': 'Only draft orders can be edited'}), 400
    
    db.session.delete(line)
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': 'Line deleted successfully'
    })

# Purchase Receipts
@purchase.route('/receipts')
@login_required
def receipts():
    receipts = PurchaseReceipt.query.order_by(PurchaseReceipt.receipt_date.desc()).all()
    return render_template('purchase/receipts.html', receipts=receipts)

@purchase.route('/orders/<int:order_id>/receive', methods=['GET', 'POST'])
@login_required
def receive_order(order_id):
    order = PurchaseOrder.query.get_or_404(order_id)
    
    # Only confirmed orders can be received
    if order.state != 'confirmed':
        flash('Only confirmed orders can be received.', 'warning')
        return redirect(url_for('purchase.view_order', order_id=order.id))
    
    # Check if all products have been received
    if order.is_fully_received:
        flash('All products in this order have already been received.', 'info')
        return redirect(url_for('purchase.view_order', order_id=order.id))
    
    form = PurchaseReceiptForm()
    
    if form.validate_on_submit():
        # Generate receipt number (e.g., REC00001)
        last_receipt = PurchaseReceipt.query.order_by(PurchaseReceipt.id.desc()).first()
        receipt_number = f"REC{(last_receipt.id + 1 if last_receipt else 1):05d}"
        
        receipt = PurchaseReceipt(
            name=receipt_number,
            purchase_order_id=order.id,
            receipt_date=form.receipt_date.data,
            notes=form.notes.data,
            state='done',
            user_id=current_user.id
        )
        
        db.session.add(receipt)
        
        # Get supplier location
        supplier_location = StockLocation.query.filter_by(usage='supplier').first()
        if not supplier_location:
            flash('Supplier location not found. Please set up your inventory locations.', 'danger')
            return redirect(url_for('purchase.view_order', order_id=order.id))
        
        # Get stock location
        stock_location = StockLocation.query.filter_by(usage='internal').first()
        if not stock_location:
            flash('Stock location not found. Please set up your inventory locations.', 'danger')
            return redirect(url_for('purchase.view_order', order_id=order.id))
        
        # Process each line
        line_ids = request.form.getlist('line_ids[]')
        product_ids = request.form.getlist('product_ids[]')
        quantities = request.form.getlist('receive_quantities[]')
        
        for i, line_id in enumerate(line_ids):
            quantity = float(quantities[i])
            if quantity <= 0:
                continue
                
            order_line = PurchaseOrderLine.query.get(line_id)
            
            # Create receipt line
            receipt_line = PurchaseReceiptLine(
                purchase_receipt_id=receipt.id,
                purchase_order_line_id=order_line.id,
                product_id=order_line.product_id,
                quantity=quantity
            )
            
            db.session.add(receipt_line)
            
            # Update order line received quantity
            order_line.received_quantity += quantity
            
            # Create stock move
            stock_move = StockMove(
                product_id=order_line.product_id,
                source_location_id=supplier_location.id,
                destination_location_id=stock_location.id,
                quantity=quantity,
                reference=f"Receipt {receipt_number} for PO {order.name}",
                state='done'  # Set to 'done' directly to update inventory
            )
            
            db.session.add(stock_move)
        
        # Check if order is fully received
        if order.is_fully_received:
            order.state = 'received'
        
        db.session.commit()
        
        # Refresh product quantities to ensure available_quantity is recalculated
        for product_id in product_ids:
            product = Product.query.get(product_id)
            db.session.refresh(product)
        
        flash('Products received successfully!', 'success')
        return redirect(url_for('purchase.view_receipt', receipt_id=receipt.id))
    
    return render_template('purchase/receive_order.html', order=order, form=form)

@purchase.route('/receipts/<int:receipt_id>')
@login_required
def view_receipt(receipt_id):
    receipt = PurchaseReceipt.query.get_or_404(receipt_id)
    return render_template('purchase/view_receipt.html', receipt=receipt)

# Purchase Invoices
@purchase.route('/invoices')
@login_required
def invoices():
    invoices = PurchaseInvoice.query.order_by(PurchaseInvoice.invoice_date.desc()).all()
    return render_template('purchase/invoices.html', invoices=invoices)

@purchase.route('/orders/<int:order_id>/invoice', methods=['GET', 'POST'])
@login_required
def create_invoice(order_id):
    order = PurchaseOrder.query.get_or_404(order_id)
    
    # Only confirmed or received orders can be invoiced
    if order.state not in ['confirmed', 'received']:
        flash('Only confirmed or received orders can be invoiced.', 'warning')
        return redirect(url_for('purchase.view_order', order_id=order.id))
    
    # Check if there are received products to invoice
    has_uninvoiced = False
    for line in order.lines:
        if line.received_quantity > line.invoiced_quantity:
            has_uninvoiced = True
            break
    
    if not has_uninvoiced:
        flash('All received products have already been invoiced.', 'info')
        return redirect(url_for('purchase.view_order', order_id=order.id))
    
    form = PurchaseInvoiceForm()
    
    if form.validate_on_submit():
        # Generate invoice number (e.g., INV00001)
        last_invoice = PurchaseInvoice.query.order_by(PurchaseInvoice.id.desc()).first()
        invoice_number = f"INV{(last_invoice.id + 1 if last_invoice else 1):05d}"
        
        invoice = PurchaseInvoice(
            name=invoice_number,
            purchase_order_id=order.id,
            supplier_id=order.supplier_id,
            invoice_date=form.invoice_date.data,
            due_date=form.due_date.data,
            reference=form.reference.data,
            notes=form.notes.data,
            state='draft' if request.form.get('action') == 'draft' else 'validated',
            user_id=current_user.id
        )
        
        db.session.add(invoice)
        
        # Process each line
        line_ids = request.form.getlist('line_ids[]')
        quantities = request.form.getlist('invoice_quantities[]')
        unit_prices = request.form.getlist('unit_prices[]')
        tax_rates = request.form.getlist('tax_rates[]')
        
        total_amount = 0
        tax_amount = 0
        
        for i, line_id in enumerate(line_ids):
            if line_id and int(line_id) > 0:
                quantity = float(quantities[i])
                if quantity <= 0:
                    continue
                    
                order_line = PurchaseOrderLine.query.get(line_id)
                unit_price = float(unit_prices[i])
                tax_rate = float(tax_rates[i])
                
                # Create invoice line
                invoice_line = PurchaseInvoiceLine(
                    purchase_invoice_id=invoice.id,
                    purchase_order_line_id=order_line.id,
                    product_id=order_line.product_id,
                    quantity=quantity,
                    unit_price=unit_price,
                    tax_rate=tax_rate
                )
                
                db.session.add(invoice_line)
                
                # Update order line invoiced quantity
                order_line.invoiced_quantity += quantity
                
                # Calculate totals
                line_subtotal = quantity * unit_price
                line_tax = line_subtotal * (tax_rate / 100)
                
                total_amount += line_subtotal
                tax_amount += line_tax
        
        # Update invoice totals
        invoice.total_amount = total_amount
        invoice.tax_amount = tax_amount
        
        db.session.commit()
        
        flash('Invoice created successfully!', 'success')
        return redirect(url_for('purchase.view_invoice', invoice_id=invoice.id))
    
    return render_template('purchase/create_invoice.html', order=order, form=form)

@purchase.route('/invoices/<int:invoice_id>')
@login_required
def view_invoice(invoice_id):
    invoice = PurchaseInvoice.query.get_or_404(invoice_id)
    return render_template('purchase/view_invoice.html', invoice=invoice)

@purchase.route('/invoices/<int:invoice_id>/validate', methods=['GET', 'POST'])
@login_required
def validate_invoice(invoice_id):
    invoice = PurchaseInvoice.query.get_or_404(invoice_id)
    
    # Only draft invoices can be validated
    if invoice.state != 'draft':
        flash('Only draft invoices can be validated.', 'warning')
        return redirect(url_for('purchase.view_invoice', invoice_id=invoice.id))
    
    # Update invoice state
    invoice.state = 'validated'
    db.session.commit()
    
    flash('Invoice validated successfully!', 'success')
    return redirect(url_for('purchase.view_invoice', invoice_id=invoice.id))

# Purchase Payments
@purchase.route('/invoices/<int:invoice_id>/pay', methods=['GET', 'POST'])
@login_required
def pay_invoice(invoice_id):
    invoice = PurchaseInvoice.query.get_or_404(invoice_id)
    
    # Only validated invoices can be paid
    if invoice.state != 'validated':
        flash('Only validated invoices can be paid.', 'warning')
        return redirect(url_for('purchase.view_invoice', invoice_id=invoice.id))
    
    form = PurchasePaymentForm()
    
    # Calculate remaining amount to pay
    total_amount = invoice.total_amount + invoice.tax_amount
    paid_amount = sum(payment.amount for payment in invoice.payments)
    remaining_amount = total_amount - paid_amount
    
    # Set default amount to remaining amount
    form.amount.data = remaining_amount
    
    if form.validate_on_submit():
        # Generate payment number (e.g., PAY00001)
        last_payment = PurchasePayment.query.order_by(PurchasePayment.id.desc()).first()
        payment_number = f"PAY{(last_payment.id + 1 if last_payment else 1):05d}"
        
        payment = PurchasePayment(
            name=payment_number,
            purchase_invoice_id=invoice.id,
            payment_date=form.payment_date.data,
            amount=form.amount.data,
            payment_method=form.payment_method.data,
            reference=form.reference.data,
            notes=form.notes.data,
            user_id=current_user.id
        )
        
        db.session.add(payment)
        
        # Check if invoice is fully paid
        new_paid_amount = paid_amount + form.amount.data
        if new_paid_amount >= total_amount:
            invoice.state = 'paid'
        
        db.session.commit()
        
        flash('Payment registered successfully!', 'success')
        return redirect(url_for('purchase.view_invoice', invoice_id=invoice.id))
    
    return render_template('purchase/payment_form.html', invoice=invoice, form=form)

# Dashboard
@purchase.route('/dashboard')
@login_required
def dashboard():
    # Get recent purchase orders
    recent_orders = PurchaseOrder.query.order_by(PurchaseOrder.order_date.desc()).limit(5).all()
    
    # Get pending receipts
    pending_receipts = PurchaseOrder.query.filter_by(state='confirmed').all()
    
    # Get unpaid invoices
    unpaid_invoices = PurchaseInvoice.query.filter_by(state='validated').all()
    
    # Get top suppliers
    top_suppliers = Supplier.query.join(PurchaseOrder).group_by(Supplier.id).order_by(db.func.count(PurchaseOrder.id).desc()).limit(5).all()
    
    return render_template(
        'purchase/dashboard.html',
        recent_orders=recent_orders,
        pending_receipts=pending_receipts,
        unpaid_invoices=unpaid_invoices,
        top_suppliers=top_suppliers
    )
