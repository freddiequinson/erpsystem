from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from extensions import db
from modules.inventory.models import Product, Category, StockMove, Warehouse, StockLocation
from modules.sales.models import Customer, SalesOrder, SalesOrderLine, Invoice
from modules.pos.models import POSOrder, POSOrderLine, POSSession
from modules.purchase.models import Supplier, PurchaseOrder, PurchaseOrderLine, PurchaseInvoice
from datetime import datetime, timedelta
import calendar
import json

reporting = Blueprint('reporting', __name__, url_prefix='/reports')

@reporting.route('/')
@login_required
def index():
    return render_template('reporting/index.html')

@reporting.route('/inventory')
@login_required
def inventory_reports():
    return render_template('reporting/inventory.html')

@reporting.route('/sales')
@login_required
def sales_reports():
    return render_template('reporting/sales.html')

@reporting.route('/purchases')
@login_required
def purchase_reports():
    return render_template('reporting/purchases.html')

@reporting.route('/financials')
@login_required
def financial_reports():
    return render_template('reporting/financials.html')

# API endpoints for report data
@reporting.route('/api/inventory/stock_levels')
@login_required
def api_inventory_stock_levels():
    products = Product.query.filter_by(is_active=True).all()
    result = []
    
    for product in products:
        # Calculate current stock
        stock_in = db.session.query(db.func.sum(StockMove.quantity)).filter(
            StockMove.product_id == product.id,
            StockMove.destination_location_id.in_(
                db.session.query(StockLocation.id).filter(StockLocation.location_type == 'internal')
            ),
            StockMove.state == 'done'
        ).scalar() or 0
        
        stock_out = db.session.query(db.func.sum(StockMove.quantity)).filter(
            StockMove.product_id == product.id,
            StockMove.source_location_id.in_(
                db.session.query(StockLocation.id).filter(StockLocation.location_type == 'internal')
            ),
            StockMove.state == 'done'
        ).scalar() or 0
        
        current_stock = stock_in - stock_out
        
        result.append({
            'id': product.id,
            'name': product.name,
            'category': product.category.name if product.category else 'Uncategorized',
            'current_stock': current_stock,
            'value': current_stock * product.cost_price
        })
    
    return jsonify(result)

@reporting.route('/api/inventory/stock_movements')
@login_required
def api_inventory_stock_movements():
    # Get date range from request
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    else:
        # Default to last 30 days
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
    
    # Get stock movements
    stock_moves = StockMove.query.filter(
        StockMove.effective_date.between(start_date, end_date),
        StockMove.state == 'done'
    ).order_by(StockMove.effective_date.desc()).all()
    
    result = []
    for move in stock_moves:
        result.append({
            'id': move.id,
            'date': move.effective_date.strftime('%Y-%m-%d'),
            'product': move.product.name,
            'quantity': move.quantity,
            'source': move.source_location.name,
            'destination': move.destination_location.name,
            'reference': move.reference,
            'type': move.reference_type
        })
    
    return jsonify(result)

@reporting.route('/api/sales/monthly')
@login_required
def api_sales_monthly():
    # Get year from request, default to current year
    year = int(request.args.get('year', datetime.utcnow().year))
    
    # Initialize monthly data
    monthly_data = [{'month': i, 'sales': 0, 'orders': 0} for i in range(1, 13)]
    
    # Get sales orders data
    sales_data = db.session.query(
        db.func.extract('month', SalesOrder.order_date).label('month'),
        db.func.sum(SalesOrder.total_amount).label('sales'),
        db.func.count(SalesOrder.id).label('orders')
    ).filter(
        db.func.extract('year', SalesOrder.order_date) == year,
        SalesOrder.state != 'cancelled'
    ).group_by(
        db.func.extract('month', SalesOrder.order_date)
    ).all()
    
    # Get POS orders data
    pos_data = db.session.query(
        db.func.extract('month', POSOrder.order_date).label('month'),
        db.func.sum(POSOrder.total_amount).label('sales'),
        db.func.count(POSOrder.id).label('orders')
    ).filter(
        db.func.extract('year', POSOrder.order_date) == year,
        POSOrder.state == 'paid'
    ).group_by(
        db.func.extract('month', POSOrder.order_date)
    ).all()
    
    # Combine data
    for data in sales_data:
        month_idx = int(data.month) - 1
        monthly_data[month_idx]['sales'] += float(data.sales or 0)
        monthly_data[month_idx]['orders'] += int(data.orders or 0)
    
    for data in pos_data:
        month_idx = int(data.month) - 1
        monthly_data[month_idx]['sales'] += float(data.sales or 0)
        monthly_data[month_idx]['orders'] += int(data.orders or 0)
    
    # Add month names
    for data in monthly_data:
        data['month_name'] = calendar.month_name[data['month']]
    
    return jsonify(monthly_data)

@reporting.route('/api/sales/top_products')
@login_required
def api_sales_top_products():
    # Get date range from request
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    limit = int(request.args.get('limit', 10))
    
    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    else:
        # Default to last 30 days
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
    
    # Combine sales order lines and POS order lines
    sales_product_data = db.session.query(
        SalesOrderLine.product_id,
        db.func.sum(SalesOrderLine.quantity).label('quantity'),
        db.func.sum(SalesOrderLine.subtotal).label('amount')
    ).join(
        SalesOrder, SalesOrderLine.order_id == SalesOrder.id
    ).filter(
        SalesOrder.order_date.between(start_date, end_date),
        SalesOrder.state != 'cancelled'
    ).group_by(
        SalesOrderLine.product_id
    ).all()
    
    pos_product_data = db.session.query(
        POSOrderLine.product_id,
        db.func.sum(POSOrderLine.quantity).label('quantity'),
        db.func.sum(POSOrderLine.subtotal).label('amount')
    ).join(
        POSOrder, POSOrderLine.order_id == POSOrder.id
    ).filter(
        POSOrder.order_date.between(start_date, end_date),
        POSOrder.state == 'paid'
    ).group_by(
        POSOrderLine.product_id
    ).all()
    
    # Combine and process data
    product_data = {}
    
    for data in sales_product_data:
        product_data[data.product_id] = {
            'product_id': data.product_id,
            'quantity': float(data.quantity or 0),
            'amount': float(data.amount or 0)
        }
    
    for data in pos_product_data:
        if data.product_id in product_data:
            product_data[data.product_id]['quantity'] += float(data.quantity or 0)
            product_data[data.product_id]['amount'] += float(data.amount or 0)
        else:
            product_data[data.product_id] = {
                'product_id': data.product_id,
                'quantity': float(data.quantity or 0),
                'amount': float(data.amount or 0)
            }
    
    # Add product names
    for product_id, data in product_data.items():
        product = Product.query.get(product_id)
        if product:
            data['name'] = product.name
            data['category'] = product.category.name if product.category else 'Uncategorized'
        else:
            data['name'] = f'Product #{product_id}'
            data['category'] = 'Unknown'
    
    # Sort by amount and limit
    result = sorted(product_data.values(), key=lambda x: x['amount'], reverse=True)[:limit]
    
    return jsonify(result)

@reporting.route('/api/purchases/monthly')
@login_required
def api_purchases_monthly():
    # Get year from request, default to current year
    year = int(request.args.get('year', datetime.utcnow().year))
    
    # Initialize monthly data
    monthly_data = [{'month': i, 'purchases': 0, 'orders': 0} for i in range(1, 13)]
    
    # Get purchase orders data
    purchase_data = db.session.query(
        db.func.extract('month', PurchaseOrder.order_date).label('month'),
        db.func.sum(PurchaseOrder.total_amount).label('purchases'),
        db.func.count(PurchaseOrder.id).label('orders')
    ).filter(
        db.func.extract('year', PurchaseOrder.order_date) == year,
        PurchaseOrder.state != 'cancelled'
    ).group_by(
        db.func.extract('month', PurchaseOrder.order_date)
    ).all()
    
    # Process data
    for data in purchase_data:
        month_idx = int(data.month) - 1
        monthly_data[month_idx]['purchases'] = float(data.purchases or 0)
        monthly_data[month_idx]['orders'] = int(data.orders or 0)
    
    # Add month names
    for data in monthly_data:
        data['month_name'] = calendar.month_name[data['month']]
    
    return jsonify(monthly_data)

@reporting.route('/api/financials/profit_loss')
@login_required
def api_financials_profit_loss():
    # Get date range from request
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    else:
        # Default to current month
        today = datetime.utcnow()
        start_date = datetime(today.year, today.month, 1)
        end_date = datetime(today.year, today.month, calendar.monthrange(today.year, today.month)[1])
    
    # Calculate total sales
    sales_total = db.session.query(db.func.sum(SalesOrder.total_amount)).filter(
        SalesOrder.order_date.between(start_date, end_date),
        SalesOrder.state != 'cancelled'
    ).scalar() or 0
    
    pos_total = db.session.query(db.func.sum(POSOrder.total_amount)).filter(
        POSOrder.order_date.between(start_date, end_date),
        POSOrder.state == 'paid'
    ).scalar() or 0
    
    total_sales = float(sales_total) + float(pos_total)
    
    # Calculate total purchases
    purchases_total = db.session.query(db.func.sum(PurchaseOrder.total_amount)).filter(
        PurchaseOrder.order_date.between(start_date, end_date),
        PurchaseOrder.state != 'cancelled'
    ).scalar() or 0
    
    total_purchases = float(purchases_total)
    
    # Calculate gross profit
    gross_profit = total_sales - total_purchases
    
    # Calculate profit margin
    profit_margin = (gross_profit / total_sales * 100) if total_sales > 0 else 0
    
    result = {
        'period': {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        },
        'sales': {
            'regular_sales': float(sales_total),
            'pos_sales': float(pos_total),
            'total_sales': total_sales
        },
        'purchases': {
            'total_purchases': total_purchases
        },
        'profit': {
            'gross_profit': gross_profit,
            'profit_margin': profit_margin
        }
    }
    
    return jsonify(result)

@reporting.route('/api/export/<report_type>')
@login_required
def api_export_report(report_type):
    # This would typically generate a CSV or Excel file
    # For now, we'll just return a message
    return jsonify({
        'success': True,
        'message': f'Export of {report_type} report would be generated here'
    })
