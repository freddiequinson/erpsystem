from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session, send_file
from flask_login import login_required, current_user
from extensions import db
from modules.inventory.models import Product, Category, Warehouse, StockLocation, StockMove, Inventory, InventoryLine, UnitOfMeasure
from modules.inventory.forms import ProductForm, CategoryForm, WarehouseForm, StockLocationForm, StockMoveForm, InventoryForm
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from config import Config
import pandas as pd
import io
import uuid
import tempfile

# Add a dictionary to store temporary uploaded files
temp_files = {}

inventory = Blueprint('inventory', __name__, url_prefix='/inventory')

# Products
@inventory.route('/products', methods=['GET', 'POST'])
@login_required
def products():
    # Define all possible columns
    all_columns = {
        'sku': 'SKU',
        'name': 'Name',
        'category': 'Category',
        'sale_price': 'Sale Price',
        'cost_price': 'Cost Price',
        'available_quantity': 'Stock',
        'min_stock': 'Min Stock',
        'max_stock': 'Max Stock',
        'is_active': 'Status',
    }
    
    # Get user's column preferences from session or use defaults
    if 'product_columns' not in session:
        session['product_columns'] = ['sku', 'name', 'category', 'sale_price', 'available_quantity', 'is_active']
    
    # Handle column customization form submission
    if request.method == 'POST' and 'customize_columns' in request.form:
        selected_columns = request.form.getlist('columns')
        if selected_columns:  # Ensure at least one column is selected
            session['product_columns'] = selected_columns
            flash('Column preferences saved', 'success')
        else:
            flash('Please select at least one column', 'warning')
    
    # Get filter parameters
    category_id = request.args.get('category_id', type=int)
    stock_filter = request.args.get('stock_filter', 'all')
    is_active = request.args.get('is_active', 'all')
    sort_by = request.args.get('sort_by', 'name')
    sort_order = request.args.get('sort_order', 'asc')
    
    # Base query
    query = Product.query
    
    # Apply category filter
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    # Apply active status filter
    if is_active == 'active':
        query = query.filter(Product.is_active == True)
    elif is_active == 'inactive':
        query = query.filter(Product.is_active == False)
    
    # Get all categories for the filter dropdown
    categories = Category.query.all()
    
    # Apply sorting
    if sort_by == 'name':
        if sort_order == 'asc':
            query = query.order_by(Product.name.asc())
        else:
            query = query.order_by(Product.name.desc())
    elif sort_by == 'sku':
        if sort_order == 'asc':
            query = query.order_by(Product.sku.asc())
        else:
            query = query.order_by(Product.sku.desc())
    elif sort_by == 'category':
        if sort_order == 'asc':
            query = query.join(Category).order_by(Category.name.asc())
        else:
            query = query.join(Category).order_by(Category.name.desc())
    elif sort_by == 'sale_price':
        if sort_order == 'asc':
            query = query.order_by(Product.sale_price.asc())
        else:
            query = query.order_by(Product.sale_price.desc())
    
    # Execute query to get all products
    all_products = query.all()
    
    # Filter by stock level (this needs to be done in Python since available_quantity is a property)
    if stock_filter == 'low_stock':
        products = []
        for product in all_products:
            try:
                qty = product.available_quantity
                if isinstance(qty, (int, float)) and qty < 5:
                    products.append(product)
            except Exception as e:
                print(f"Error checking product {product.name}: {str(e)}")
    elif stock_filter == 'out_of_stock':
        products = []
        for product in all_products:
            try:
                qty = product.available_quantity
                if isinstance(qty, (int, float)) and qty <= 0:
                    products.append(product)
            except Exception as e:
                print(f"Error checking product {product.name}: {str(e)}")
    elif stock_filter == 'in_stock':
        products = []
        for product in all_products:
            try:
                qty = product.available_quantity
                if isinstance(qty, (int, float)) and qty > 0:
                    products.append(product)
            except Exception as e:
                print(f"Error checking product {product.name}: {str(e)}")
    else:
        products = all_products
    
    # If sorting by available_quantity, we need to do it in Python
    if sort_by == 'available_quantity':
        try:
            products.sort(
                key=lambda p: p.available_quantity if isinstance(p.available_quantity, (int, float)) else float('inf'),
                reverse=(sort_order == 'desc')
            )
        except Exception as e:
            print(f"Error sorting by available_quantity: {str(e)}")
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Number of items per page
    pagination = query.order_by(Product.name).paginate(page=page, per_page=per_page, error_out=False)
    paginated_products = pagination.items
    
    return render_template(
        'inventory/products.html', 
        products=paginated_products, 
        all_columns=all_columns,
        selected_columns=session['product_columns'],
        categories=categories,
        current_category_id=category_id,
        current_stock_filter=stock_filter,
        current_is_active=is_active,
        current_sort_by=sort_by,
        current_sort_order=sort_order,
        pagination=pagination
    )

@inventory.route('/products/new', methods=['GET', 'POST'])
@login_required
def new_product():
    form = ProductForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    form.uom_id.choices = [(u.id, u.name) for u in UnitOfMeasure.query.all()]
    
    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            description=form.description.data,
            sku=form.sku.data,
            barcode=form.barcode.data,
            category_id=form.category_id.data,
            uom_id=form.uom_id.data,
            cost_price=form.cost_price.data,
            sale_price=form.sale_price.data,
            min_stock=form.min_stock.data,
            max_stock=form.max_stock.data,
            weight=form.weight.data,
            volume=form.volume.data,
            is_active=form.is_active.data
        )
        
        # Handle image upload
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            # Create a unique filename
            unique_filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
            filepath = os.path.join(Config.UPLOAD_FOLDER, 'products', unique_filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            form.image.data.save(filepath)
            product.image_path = f'/static/uploads/products/{unique_filename}'
        
        db.session.add(product)
        db.session.commit()
        
        flash('Product created successfully!', 'success')
        return redirect(url_for('inventory.products'))
    
    return render_template('inventory/product_form.html', form=form, title='New Product')

@inventory.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    form.uom_id.choices = [(u.id, u.name) for u in UnitOfMeasure.query.all()]
    
    if form.validate_on_submit():
        form.populate_obj(product)
        
        # Handle image upload
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            # Create a unique filename
            unique_filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
            filepath = os.path.join(Config.UPLOAD_FOLDER, 'products', unique_filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            form.image.data.save(filepath)
            product.image_path = f'/static/uploads/products/{unique_filename}'
        
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('inventory.products'))
    
    return render_template('inventory/product_form.html', form=form, title='Edit Product', product=product)

@inventory.route('/products/<int:product_id>/view', methods=['GET'])
@login_required
def view_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Get stock moves for this product
    stock_moves = StockMove.query.filter_by(product_id=product_id).order_by(StockMove.date.desc()).limit(10).all()
    
    # Get stock by location
    stock_by_location = []
    locations = StockLocation.query.filter_by(usage='internal').all()
    for location in locations:
        quantity = product.get_quantity_at_location(location.id)
        if quantity != 0:  # Only show locations with stock
            stock_by_location.append({
                'location': location,
                'quantity': quantity
            })
    
    return render_template(
        'inventory/product_view.html', 
        product=product, 
        stock_moves=stock_moves,
        stock_by_location=stock_by_location
    )

@inventory.route('/products/<int:product_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Check if product has any stock moves
    stock_moves = StockMove.query.filter_by(product_id=product_id).first()
    if stock_moves:
        flash('Cannot delete product that has stock movements. Consider marking it as inactive instead.', 'danger')
        return redirect(url_for('inventory.products'))
    
    # Get product name before deletion for flash message
    product_name = product.name
    
    # Delete the product
    db.session.delete(product)
    db.session.commit()
    
    flash(f'Product "{product_name}" has been deleted.', 'success')
    return redirect(url_for('inventory.products'))

@inventory.route('/clear-all-products', methods=['POST'])
@login_required
def clear_all_products():
    """Clear all products from the database"""
    try:
        # First delete all inventory lines
        InventoryLine.query.delete()
        db.session.commit()
        
        # Then delete all inventory records
        Inventory.query.delete()
        db.session.commit()
        
        # Delete all stock moves
        StockMove.query.delete()
        db.session.commit()
        
        # Finally delete all products
        Product.query.delete()
        db.session.commit()
        
        flash('All products and related inventory data have been cleared successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error clearing products: {str(e)}', 'danger')
    
    return redirect(url_for('inventory.products'))

# Categories
@inventory.route('/categories')
@login_required
def categories():
    categories = Category.query.all()
    return render_template('inventory/categories.html', categories=categories)

@inventory.route('/categories/new', methods=['GET', 'POST'])
@login_required
def new_category():
    form = CategoryForm()
    form.parent_id.choices = [(0, 'None')] + [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            description=form.description.data,
            parent_id=form.parent_id.data if form.parent_id.data != 0 else None
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash('Category created successfully!', 'success')
        return redirect(url_for('inventory.categories'))
    
    return render_template('inventory/category_form.html', form=form, title='New Category')

@inventory.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)
    
    # Exclude the current category from parent choices to prevent circular references
    form.parent_id.choices = [(0, 'None')] + [(c.id, c.name) for c in Category.query.filter(Category.id != category_id).all()]
    
    if form.validate_on_submit():
        category.name = form.name.data
        category.description = form.description.data
        category.parent_id = form.parent_id.data if form.parent_id.data != 0 else None
        
        db.session.commit()
        flash('Category updated successfully!', 'success')
        return redirect(url_for('inventory.categories'))
    
    # Set the current parent_id value for the form
    if category.parent_id:
        form.parent_id.data = category.parent_id
    else:
        form.parent_id.data = 0
    
    return render_template('inventory/category_form.html', form=form, title='Edit Category', category=category)

@inventory.route('/categories/<int:category_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    
    # Check if category has products
    if category.products.count() > 0:
        # Option 1: Prevent deletion
        # flash(f'Cannot delete category "{category.name}" because it has {category.products.count()} products associated with it.', 'danger')
        # return redirect(url_for('inventory.categories'))
        
        # Option 2: Set products' category to None
        for product in category.products:
            product.category_id = None
    
    # Check if category has child categories
    child_categories = Category.query.filter_by(parent_id=category.id).all()
    if child_categories:
        for child in child_categories:
            # Set child categories' parent to the parent of the category being deleted
            child.parent_id = category.parent_id
    
    # Get category name before deletion for flash message
    category_name = category.name
    
    # Delete the category
    db.session.delete(category)
    db.session.commit()
    
    flash(f'Category "{category_name}" has been deleted.', 'success')
    return redirect(url_for('inventory.categories'))

# Stock Movements
@inventory.route('/stock-moves')
@login_required
def stock_moves():
    stock_moves = StockMove.query.order_by(StockMove.created_at.desc()).all()
    return render_template('inventory/stock_moves.html', stock_moves=stock_moves)

@inventory.route('/stock-moves/new', methods=['GET', 'POST'])
@login_required
def new_stock_move():
    form = StockMoveForm()
    form.product_id.choices = [(p.id, p.name) for p in Product.query.filter_by(is_active=True).all()]
    form.source_location_id.choices = [(l.id, l.name) for l in StockLocation.query.all()]
    form.destination_location_id.choices = [(l.id, l.name) for l in StockLocation.query.all()]
    
    # Pre-select product if product_id is provided in the URL
    product_id = request.args.get('product_id', type=int)
    if product_id and request.method == 'GET':
        form.product_id.data = product_id
        
        # Pre-select appropriate locations for restocking
        # Find supplier location for source
        supplier_location = StockLocation.query.filter_by(location_type='supplier').first()
        if supplier_location:
            form.source_location_id.data = supplier_location.id
            
        # Find internal location for destination
        internal_location = StockLocation.query.filter_by(location_type='internal').first()
        if internal_location:
            form.destination_location_id.data = internal_location.id
    
    if form.validate_on_submit():
        stock_move = StockMove(
            product_id=form.product_id.data,
            source_location_id=form.source_location_id.data,
            destination_location_id=form.destination_location_id.data,
            quantity=form.quantity.data,
            state='draft',
            reference=form.reference.data,
            reference_type=form.reference_type.data,
            scheduled_date=form.scheduled_date.data
        )
        
        db.session.add(stock_move)
        db.session.commit()
        
        flash('Stock move created successfully!', 'success')
        return redirect(url_for('inventory.stock_moves'))
    
    return render_template('inventory/stock_move_form.html', form=form, title='New Stock Move')

@inventory.route('/stock-moves/<int:move_id>/validate', methods=['GET', 'POST'])
@login_required
def validate_stock_move(move_id):
    stock_move = StockMove.query.get_or_404(move_id)
    
    if stock_move.state != 'draft':
        flash('Only draft stock moves can be validated', 'warning')
        return redirect(url_for('inventory.stock_moves'))
    
    # Update product quantities
    product = stock_move.product
    source_location = stock_move.source_location
    destination_location = stock_move.destination_location
    
    # Check if source or destination is an internal location
    source_is_internal = source_location.location_type == 'internal'
    destination_is_internal = destination_location.location_type == 'internal'
    
    # Update the state and effective date
    stock_move.state = 'done'
    stock_move.effective_date = datetime.utcnow()
    
    db.session.commit()
    
    # Force refresh of product cache to ensure available_quantity is recalculated
    db.session.refresh(product)
    
    flash('Stock movement validated successfully', 'success')
    return redirect(url_for('inventory.stock_moves'))

@inventory.route('/stock-moves/<int:move_id>/cancel', methods=['GET', 'POST'])
@login_required
def cancel_stock_move(move_id):
    stock_move = StockMove.query.get_or_404(move_id)
    
    if stock_move.state != 'draft':
        flash('Only draft stock moves can be cancelled', 'warning')
        return redirect(url_for('inventory.stock_moves'))
    
    # Update the state
    stock_move.state = 'cancelled'
    
    db.session.commit()
    flash('Stock movement cancelled', 'success')
    return redirect(url_for('inventory.stock_moves'))

# Inventory Adjustments
@inventory.route('/inventories')
@login_required
def inventories():
    inventories = Inventory.query.order_by(Inventory.created_at.desc()).all()
    return render_template('inventory/inventories.html', inventories=inventories)

@inventory.route('/inventories/new', methods=['GET', 'POST'])
@login_required
def new_inventory():
    form = InventoryForm()
    form.location_id.choices = [(l.id, l.name) for l in StockLocation.query.filter_by(location_type='internal').all()]
    
    if form.validate_on_submit():
        inventory = Inventory(
            name=form.name.data,
            location_id=form.location_id.data,
            state='draft',
            created_at=datetime.utcnow()
        )
        
        db.session.add(inventory)
        db.session.commit()
        
        # Create inventory lines for all products
        location = StockLocation.query.get(form.location_id.data)
        products = Product.query.filter_by(is_active=True).all()
        
        for product in products:
            theoretical_qty = product.available_quantity
            inventory_line = InventoryLine(
                inventory_id=inventory.id,
                product_id=product.id,
                theoretical_qty=theoretical_qty,
                product_qty=theoretical_qty  # Initialize with theoretical quantity
            )
            db.session.add(inventory_line)
        
        db.session.commit()
        
        flash('Inventory created successfully!', 'success')
        return redirect(url_for('inventory.edit_inventory', inventory_id=inventory.id))
    
    return render_template('inventory/inventory_form.html', form=form, title='New Inventory')

@inventory.route('/inventories/<int:inventory_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_inventory(inventory_id):
    inventory = Inventory.query.get_or_404(inventory_id)
    
    if inventory.state != 'draft':
        flash('Cannot edit validated inventory.', 'danger')
        return redirect(url_for('inventory.inventories'))
    
    return render_template('inventory/inventory_edit.html', inventory=inventory)

@inventory.route('/inventories/<int:inventory_id>/validate', methods=['POST'])
@login_required
def validate_inventory(inventory_id):
    inventory = Inventory.query.get_or_404(inventory_id)
    
    if inventory.state != 'draft':
        flash('Inventory already validated or cancelled.', 'danger')
        return redirect(url_for('inventory.inventories'))
    
    # Create stock moves for inventory adjustments
    for line in inventory.lines:
        diff = line.product_qty - line.theoretical_qty
        
        if diff != 0:
            # Determine source and destination based on whether it's a positive or negative adjustment
            if diff > 0:
                # Positive adjustment (increase stock)
                source_location = StockLocation.query.filter_by(location_type='inventory_loss').first()
                destination_location = inventory.location
            else:
                # Negative adjustment (decrease stock)
                source_location = inventory.location
                destination_location = StockLocation.query.filter_by(location_type='inventory_loss').first()
            
            stock_move = StockMove(
                product_id=line.product_id,
                source_location_id=source_location.id,
                destination_location_id=destination_location.id,
                quantity=abs(diff),
                state='done',
                reference=f"INV-{inventory.id}",
                reference_type='inventory',
                effective_date=datetime.utcnow()
            )
            
            db.session.add(stock_move)
    
    inventory.state = 'validated'
    inventory.validated_at = datetime.utcnow()
    db.session.commit()
    
    flash('Inventory validated successfully!', 'success')
    return redirect(url_for('inventory.inventories'))

@inventory.route('/inventories/<int:inventory_id>/cancel', methods=['POST'])
@login_required
def cancel_inventory(inventory_id):
    inventory = Inventory.query.get_or_404(inventory_id)
    
    if inventory.state == 'validated':
        flash('Cannot cancel validated inventory.', 'danger')
        return redirect(url_for('inventory.inventories'))
    
    inventory.state = 'cancelled'
    db.session.commit()
    
    flash('Inventory cancelled successfully!', 'success')
    return redirect(url_for('inventory.inventories'))

# API endpoints for AJAX calls
@inventory.route('/api/inventory-lines/<int:inventory_id>', methods=['GET'])
@login_required
def api_inventory_lines(inventory_id):
    inventory = Inventory.query.get_or_404(inventory_id)
    lines = []
    
    for line in inventory.lines:
        lines.append({
            'id': line.id,
            'product_id': line.product_id,
            'product_name': line.product.name,
            'theoretical_qty': line.theoretical_qty,
            'product_qty': line.product_qty
        })
    
    return jsonify(lines)

@inventory.route('/api/inventory-lines/<int:line_id>/update', methods=['POST'])
@login_required
def api_update_inventory_line(line_id):
    line = InventoryLine.query.get_or_404(line_id)
    
    if line.inventory.state != 'draft':
        return jsonify({'success': False, 'message': 'Cannot update validated inventory'}), 400
    
    data = request.json
    line.product_qty = data.get('product_qty', line.product_qty)
    db.session.commit()
    
    return jsonify({'success': True})

# Excel Import/Export
@inventory.route('/import-export')
@login_required
def import_export():
    return render_template('inventory/import_export.html')

@inventory.route('/preview-excel', methods=['POST'])
@login_required
def preview_excel():
    if 'excel_file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['excel_file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in ['xlsx', 'xls']:
        try:
            # Save file to temporary location
            temp_dir = tempfile.gettempdir()
            file_id = str(uuid.uuid4())
            file_path = os.path.join(temp_dir, f"{file_id}.xlsx")
            file.save(file_path)
            
            # Store file path for later use
            temp_files[file_id] = {
                'path': file_path,
                'created_at': datetime.now()
            }
            
            # Read Excel file
            has_header = request.form.get('has_header', 'true') == 'true'
            df = pd.read_excel(file_path, header=0 if has_header else None)
            
            # Get column names (either from header or generated)
            columns = df.columns.tolist() if has_header else [f"Column {i+1}" for i in range(df.shape[1])]
            
            # Get preview data (first 5 rows)
            # Convert to Python native types and handle NaN/None values
            preview_data = []
            for _, row in df.head(5).iterrows():
                row_data = []
                for val in row:
                    if pd.isna(val) or val is None:
                        row_data.append("")
                    elif isinstance(val, (int, float, str, bool)):
                        row_data.append(val)
                    else:
                        # Convert any other types to string
                        row_data.append(str(val))
                preview_data.append(row_data)
            
            return jsonify({
                'file_id': file_id,
                'columns': columns,
                'preview_data': preview_data
            })
            
        except Exception as e:
            print(f"Error in preview_excel: {str(e)}")
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Allowed file types are xlsx and xls'}), 400

@inventory.route('/import-products', methods=['POST'])
@login_required
def import_products():
    # Check if it's a direct upload or from the mapping form
    if 'excel_file' in request.files:
        # Direct file upload (old method)
        file = request.files['excel_file']
        
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(url_for('inventory.import_export'))
        
        if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in ['xlsx', 'xls']:
            try:
                # Read Excel file
                df = pd.read_excel(file)
                
                # Process data without mapping
                return process_product_import(df)
            except Exception as e:
                flash(f'Error processing file: {str(e)}', 'danger')
                return redirect(url_for('inventory.import_export'))
        else:
            flash('Allowed file types are xlsx and xls', 'danger')
            return redirect(url_for('inventory.import_export'))
    
    elif 'file_data' in request.form:
        # Import with column mapping
        file_id = request.form.get('file_data')
        
        if file_id not in temp_files:
            flash('File upload expired or invalid. Please try again.', 'danger')
            return redirect(url_for('inventory.import_export'))
        
        try:
            # Get the file path
            file_path = temp_files[file_id]['path']
            
            # Read Excel file
            has_header = request.form.get('has_header', 'true') == 'true'
            df = pd.read_excel(file_path, header=0 if has_header else None)
            
            # Apply column mapping
            mapping = {}
            print("Form data:", request.form)  # Debug print
            
            for field, column_index in request.form.items():
                if field.startswith('mapping[') and field.endswith(']'):
                    field_name = field[8:-1]  # Extract field name from mapping[field_name]
                    if column_index and column_index.strip():  # Only map if a column was selected
                        mapping[field_name] = int(column_index)
            
            # Create a new DataFrame with mapped columns
            mapped_df = pd.DataFrame()
            
            print(f"Mapping: {mapping}")  # Debug print
            
            # Check if required fields are mapped
            required_fields = ['name', 'sku']
            missing_fields = [field for field in required_fields if field not in mapping]
            
            if missing_fields:
                flash(f"Required fields not mapped: {', '.join(missing_fields)}", 'danger')
                return redirect(url_for('inventory.import_export'))
            
            # Apply mapping
            for field, column_index in mapping.items():
                mapped_df[field] = df.iloc[:, int(column_index)]
            
            # Debug print
            print(f"Mapped columns: {mapped_df.columns.tolist()}")
            
            # Clean up the temporary file
            os.remove(file_path)
            del temp_files[file_id]
            
            # Process the mapped DataFrame
            return process_product_import(mapped_df)
            
        except Exception as e:
            print(f"Error in import_products: {str(e)}")  # Debug print
            flash(f'Error processing file: {str(e)}', 'danger')
            return redirect(url_for('inventory.import_export'))
    
    else:
        flash('No file data provided', 'danger')
        return redirect(url_for('inventory.import_export'))

def process_product_import(df):
    """Process the product import from a DataFrame"""
    try:
        # Debug print
        print(f"Columns in dataframe: {df.columns.tolist()}")
        
        # Map Odoo column names to our database fields if they exist
        column_mapping = {
            'Product Name': 'name',
            'Cost Price': 'cost_price',
            'Sales Price': 'sale_price',
            'Quantity on Hand': 'quantity',
            'Warehouse': 'warehouse',
            'POS Category': 'pos_category',
            'Category': 'category',
            'Available in POS': 'available_in_pos',
            'SKU': 'sku'
        }
        
        # Rename columns that match our mapping
        for odoo_col, our_col in column_mapping.items():
            if odoo_col in df.columns:
                df = df.rename(columns={odoo_col: our_col})
        
        # Debug print after renaming
        print(f"Columns after renaming: {df.columns.tolist()}")
        
        # Check if required columns exist
        required_columns = ['name', 'sku']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            flash(f"Missing required columns: {', '.join(missing_columns)}", 'danger')
            return redirect(url_for('inventory.import_export'))
        
        # Process data
        products_created = 0
        products_updated = 0
        warehouses_created = 0
        categories_created = 0
        pos_categories_created = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Check if product exists by SKU
                product = Product.query.filter_by(sku=row['sku']).first()
                
                # Get or create category if it exists in the data
                category_id = None
                if 'category' in df.columns and not pd.isna(row['category']):
                    category = Category.query.filter_by(name=row['category']).first()
                    if not category:
                        category = Category(name=row['category'])
                        db.session.add(category)
                        db.session.commit()
                        categories_created += 1
                    category_id = category.id
                
                # Get or create warehouse if it exists in the data
                warehouse_id = None
                if 'warehouse' in df.columns and not pd.isna(row['warehouse']):
                    warehouse = Warehouse.query.filter_by(name=row['warehouse']).first()
                    if not warehouse:
                        try:
                            # Try to create warehouse with is_active parameter
                            warehouse = Warehouse(
                                name=row['warehouse'],
                                code=row['warehouse'][:5].upper(),
                                address=f"{row['warehouse']} Address",
                                is_active=True
                            )
                        except TypeError:
                            # If is_active is not a valid parameter, create without it
                            warehouse = Warehouse(
                                name=row['warehouse'],
                                code=row['warehouse'][:5].upper(),
                                address=f"{row['warehouse']} Address"
                            )
                        
                        db.session.add(warehouse)
                        db.session.commit()
                        
                        # Create default stock location for the warehouse
                        try:
                            # Try to create stock location with is_active parameter
                            stock_location = StockLocation(
                                name=f"{warehouse.name} Stock",
                                code=f"STOCK-{warehouse.code}",
                                warehouse_id=warehouse.id,
                                is_active=True
                            )
                        except TypeError:
                            # If is_active is not a valid parameter, create without it
                            stock_location = StockLocation(
                                name=f"{warehouse.name} Stock",
                                code=f"STOCK-{warehouse.code}",
                                warehouse_id=warehouse.id
                            )
                        
                        db.session.add(stock_location)
                        db.session.commit()
                        warehouses_created += 1
                    warehouse_id = warehouse.id
                
                # Get default UOM if not specified
                try:
                    # Try to get the default 'Unit' UOM
                    default_uom = UnitOfMeasure.query.filter_by(name='Unit').first()
                    if not default_uom:
                        # Create a default UOM if it doesn't exist
                        default_uom = UnitOfMeasure(
                            name='Unit', 
                            code='UNT',
                            category='unit',  
                            ratio=1.0
                        )
                        db.session.add(default_uom)
                        db.session.commit()
                    uom_id = default_uom.id
                except Exception as e:
                    print(f"Error getting/creating UOM: {str(e)}")
                    # Rollback the session if there was an error
                    db.session.rollback()
                    # Try to find any existing UOM to use as fallback
                    any_uom = UnitOfMeasure.query.first()
                    uom_id = any_uom.id if any_uom else 1
                
                if product:
                    # Update existing product
                    if 'name' in df.columns and not pd.isna(row['name']):
                        product.name = row['name']
                    if category_id:
                        product.category_id = category_id
                    if 'cost_price' in df.columns and not pd.isna(row['cost_price']):
                        product.cost_price = float(row['cost_price'])
                    if 'sale_price' in df.columns and not pd.isna(row['sale_price']):
                        product.sale_price = float(row['sale_price'])
                    
                    # Optional fields
                    if 'description' in df.columns and not pd.isna(row['description']):
                        product.description = row['description']
                    if 'barcode' in df.columns and not pd.isna(row['barcode']):
                        product.barcode = row['barcode']
                    if 'min_stock' in df.columns and not pd.isna(row['min_stock']):
                        product.min_stock = float(row['min_stock'])
                    if 'max_stock' in df.columns and not pd.isna(row['max_stock']):
                        product.max_stock = float(row['max_stock'])
                    if 'weight' in df.columns and not pd.isna(row['weight']):
                        product.weight = float(row['weight'])
                    if 'volume' in df.columns and not pd.isna(row['volume']):
                        product.volume = float(row['volume'])
                    if 'is_active' in df.columns and not pd.isna(row['is_active']):
                        product.is_active = bool(row['is_active'])
                    if 'available_in_pos' in df.columns and not pd.isna(row['available_in_pos']):
                        product.available_in_pos = bool(row['available_in_pos'])
                    
                    products_updated += 1
                else:
                    # Create new product with required fields
                    new_product = Product(
                        name=row['name'],
                        sku=row['sku'],
                        uom_id=uom_id
                    )
                    
                    # Set optional fields if they exist in the data
                    if category_id:
                        new_product.category_id = category_id
                    if 'cost_price' in df.columns and not pd.isna(row['cost_price']):
                        new_product.cost_price = float(row['cost_price'])
                    if 'sale_price' in df.columns and not pd.isna(row['sale_price']):
                        new_product.sale_price = float(row['sale_price'])
                    if 'description' in df.columns and not pd.isna(row['description']):
                        new_product.description = row['description']
                    if 'barcode' in df.columns and not pd.isna(row['barcode']):
                        new_product.barcode = row['barcode']
                    if 'min_stock' in df.columns and not pd.isna(row['min_stock']):
                        new_product.min_stock = float(row['min_stock'])
                    if 'max_stock' in df.columns and not pd.isna(row['max_stock']):
                        new_product.max_stock = float(row['max_stock'])
                    if 'weight' in df.columns and not pd.isna(row['weight']):
                        new_product.weight = float(row['weight'])
                    if 'volume' in df.columns and not pd.isna(row['volume']):
                        new_product.volume = float(row['volume'])
                    if 'is_active' in df.columns and not pd.isna(row['is_active']):
                        new_product.is_active = bool(row['is_active'])
                    if 'available_in_pos' in df.columns and not pd.isna(row['available_in_pos']):
                        new_product.available_in_pos = bool(row['available_in_pos'])
                    
                    db.session.add(new_product)
                    db.session.commit()
                    product = new_product
                    products_created += 1
                
                # Handle stock quantity updates if different from current
                if 'quantity' in df.columns and not pd.isna(row['quantity']):
                    # Get the current quantity
                    current_quantity = product.available_quantity
                    target_quantity = float(row['quantity'])
                    
                    # Only create a stock move if the quantities are different
                    if target_quantity != current_quantity:
                        # Find or create a warehouse if not specified
                        if not warehouse_id:
                            warehouse = Warehouse.query.first()
                            if not warehouse:
                                # Create a default warehouse if none exists
                                warehouse = Warehouse(
                                    name='Main Warehouse',
                                    code='MAIN',
                                    address='Default Address'
                                )
                                db.session.add(warehouse)
                                db.session.commit()
                                
                                # Create default stock location
                                stock_location = StockLocation(
                                    name='Main Stock',
                                    warehouse_id=warehouse.id,
                                    location_type='internal'
                                )
                                db.session.add(stock_location)
                                db.session.commit()
                            warehouse_id = warehouse.id
                        
                        # Get the warehouse's stock location
                        stock_location = StockLocation.query.filter_by(warehouse_id=warehouse_id, location_type='internal').first()
                        if not stock_location:
                            # Create a stock location if none exists
                            warehouse = Warehouse.query.get(warehouse_id)
                            stock_location = StockLocation(
                                name=f"{warehouse.name} Stock",
                                warehouse_id=warehouse_id,
                                location_type='internal'
                            )
                            db.session.add(stock_location)
                            db.session.commit()
                        
                        # Create a supplier location if it doesn't exist
                        supplier_location = StockLocation.query.filter_by(location_type='supplier').first()
                        if not supplier_location:
                            supplier_location = StockLocation(
                                name='Supplier',
                                location_type='supplier'
                            )
                            db.session.add(supplier_location)
                            db.session.commit()
                        
                        # Create an inventory loss location if it doesn't exist
                        inventory_loss_location = StockLocation.query.filter_by(location_type='inventory_loss').first()
                        if not inventory_loss_location:
                            inventory_loss_location = StockLocation(
                                name='Inventory Loss',
                                location_type='inventory_loss'
                            )
                            db.session.add(inventory_loss_location)
                            db.session.commit()
                        
                        # Determine if we need to add or remove stock
                        if target_quantity > current_quantity:
                            # Add stock: from supplier to stock location
                            quantity_to_move = target_quantity - current_quantity
                            source_location = supplier_location
                            destination_location = stock_location
                        else:
                            # Remove stock: from stock location to inventory loss
                            quantity_to_move = current_quantity - target_quantity
                            source_location = stock_location
                            destination_location = inventory_loss_location
                        
                        # Create the stock move
                        stock_move = StockMove(
                            product_id=product.id,
                            source_location_id=source_location.id,
                            destination_location_id=destination_location.id,
                            quantity=quantity_to_move,
                            state='done',
                            reference=f"Stock adjustment from import",
                            reference_type='import',
                            effective_date=datetime.utcnow()
                        )
                        db.session.add(stock_move)
                        db.session.commit()
            
            except Exception as e:
                errors.append(f"Error on row {index + 2}: {str(e)}")
        
        # Commit all changes
        db.session.commit()
        
        # Flash messages
        if products_created > 0:
            flash(f'Successfully created {products_created} products', 'success')
        if products_updated > 0:
            flash(f'Successfully updated {products_updated} products', 'success')
        if warehouses_created > 0:
            flash(f'Created {warehouses_created} new warehouses', 'success')
        if categories_created > 0:
            flash(f'Created {categories_created} new categories', 'success')
        if errors:
            for error in errors[:5]:  # Show only first 5 errors
                flash(error, 'warning')
            if len(errors) > 5:
                flash(f'...and {len(errors) - 5} more errors', 'warning')
        
        return redirect(url_for('inventory.products'))
    
    except Exception as e:
        flash(f'Error processing file: {str(e)}', 'danger')
        return redirect(url_for('inventory.import_export'))

@inventory.route('/export-products')
@login_required
def export_products():
    products = Product.query.all()
    
    # Create DataFrame
    data = []
    for product in products:
        # Get product's warehouse and stock quantity
        warehouse_name = ""
        quantity = product.available_quantity
        
        # Get the first warehouse for simplicity
        warehouse = Warehouse.query.first()
        if warehouse:
            warehouse_name = warehouse.name
        
        # Format data in Odoo-like format
        data.append({
            'Product Name': product.name,
            'Cost Price': product.cost_price,
            'Sales Price': product.sale_price,
            'Quantity on Hand': quantity,
            'Warehouse': warehouse_name,
            'POS Category': product.category.name if product.category else '',
            'Category': product.category.name if product.category else '',
            'Available in POS': getattr(product, 'available_in_pos', True),
            'SKU': product.sku,
            'Barcode': product.barcode or '',
            'Description': product.description or '',
            'Min Stock': product.min_stock,
            'Max Stock': product.max_stock,
            'Weight': product.weight,
            'Volume': product.volume,
            'Is Active': product.is_active
        })
    
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Products', index=False)
        
        # Auto-adjust columns' width
        worksheet = writer.sheets['Products']
        for i, col in enumerate(df.columns):
            column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, column_width)
    
    output.seek(0)
    
    # Return Excel file as response
    from flask import send_file
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'products_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    )

@inventory.route('/download-template')
@login_required
def download_template():
    # Create template DataFrame with Odoo-like format
    template_data = {
        'Product Name': ['Screen 557', 'Screen 559', 'Screen 572'],
        'Cost Price': [80, 90, 120],
        'Sales Price': [100, 110, 150],
        'Quantity on Hand': [8, 41, 0],
        'Warehouse': ['Tyssone Electronics', 'Tyssone Electronics', 'Tyssone Electronics'],
        'POS Category': ['SCREENS', 'SCREENS', 'SCREENS'],
        'Category': ['SCREENS', 'SCREENS', 'SCREENS'],
        'Available in POS': [True, True, True],
        'SKU': ['557', '559', '572'],
        'Barcode': ['557000', '559000', '572000'],
        'Description': ['Screen 557 Description', 'Screen 559 Description', 'Screen 572 Description'],
        'Min Stock': [5, 5, 5],
        'Max Stock': [100, 100, 100],
        'Weight': [1.5, 1.6, 1.7],
        'Volume': [0.1, 0.1, 0.1],
        'Is Active': [True, True, True]
    }
    
    df = pd.DataFrame(template_data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Template', index=False)
        
        # Auto-adjust columns' width
        worksheet = writer.sheets['Template']
        for i, col in enumerate(df.columns):
            column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, column_width)
        
        # Add instructions sheet
        instructions = pd.DataFrame({
            'Field': df.columns.tolist(),
            'Required': ['Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'No', 'No', 'No', 'No', 'No', 'No', 'No'],
            'Description': [
                'Product name (required)',
                'Product cost price (required)',
                'Product sale price (required)',
                'Current stock quantity (required)',
                'Warehouse name (required)',
                'POS category name (required)',
                'Product category name (required)',
                'Whether product is available in POS (True/False) (required)',
                'Unique product identifier (required)',
                'Product barcode (optional)',
                'Product description (optional)',
                'Minimum stock level (optional)',
                'Maximum stock level (optional)',
                'Product weight (optional)',
                'Product volume (optional)',
                'Is product active (True/False) (optional)'
            ]
        })
        
        instructions.to_excel(writer, sheet_name='Instructions', index=False)
        
        # Auto-adjust columns' width for instructions
        worksheet = writer.sheets['Instructions']
        for i, col in enumerate(instructions.columns):
            column_width = max(instructions[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, column_width)
    
    output.seek(0)
    
    # Return Excel file as response
    from flask import send_file
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='product_import_template.xlsx'
    )

# Low Stock Report
@inventory.route('/low-stock-report')
@login_required
def low_stock_report():
    try:
        # Get all active products
        all_products = Product.query.filter(Product.is_active == True).all()
        
        # Filter for low stock products (less than 5 units)
        low_stock = []
        for product in all_products:
            try:
                qty = product.available_quantity
                if isinstance(qty, (int, float)) and qty < 5:
                    low_stock.append(product)
            except Exception as e:
                print(f"Error checking product {product.name}: {str(e)}")
        
        # Sort by available quantity
        low_stock.sort(key=lambda p: p.available_quantity if isinstance(p.available_quantity, (int, float)) else float('inf'))
        
        # Create a DataFrame for the report
        data = []
        for product in low_stock:
            # Get sales data for this product (from POS order lines)
            from modules.pos.models import POSOrderLine
            order_lines = POSOrderLine.query.filter_by(product_id=product.id).all()
            sales_count = len(order_lines)
            
            # Calculate revenue from this product (subtotal is a property, not a column)
            revenue = sum(line.subtotal for line in order_lines)
            
            # Get stock movements for this product to determine initial stock
            from sqlalchemy import and_
            inbound_moves = StockMove.query.filter(
                and_(
                    StockMove.product_id == product.id,
                    StockMove.state == 'done',
                    StockMove.destination_location.has(StockLocation.location_type == 'internal')
                )
            ).all()
            
            outbound_moves = StockMove.query.filter(
                and_(
                    StockMove.product_id == product.id,
                    StockMove.state == 'done',
                    StockMove.source_location.has(StockLocation.location_type == 'internal')
                )
            ).all()
            
            # Calculate total inbound and outbound quantities
            total_inbound = sum(move.quantity for move in inbound_moves)
            total_outbound = sum(move.quantity for move in outbound_moves)
            
            # Initial stock = current stock + outbound - inbound
            initial_stock = product.available_quantity + total_outbound - total_inbound
            
            # Determine if product needs reordering
            needs_reorder = product.available_quantity <= (product.min_stock or 0)
            
            data.append({
                'sku': product.sku,
                'name': product.name,
                'category': product.category.name if product.category else 'Uncategorized',
                'current_stock': product.available_quantity,
                'initial_stock': initial_stock,
                'min_stock': product.min_stock or 0,
                'max_stock': product.max_stock or 0,
                'sales_count': sales_count,
                'revenue': revenue,
                'cost_price': product.cost_price or 0,
                'sale_price': product.sale_price or 0,
                'profit_margin': ((product.sale_price or 0) - (product.cost_price or 0)) / (product.cost_price or 1) * 100 if product.cost_price else 0,
                'needs_reorder': 'Yes' if needs_reorder else 'No'
            })
        
        if not data:
            flash('No low stock products found', 'warning')
            return redirect(url_for('inventory.products'))
        
        # Create Excel file
        import pandas as pd
        from io import BytesIO
        
        df = pd.DataFrame(data)
        
        # Reorder columns for better readability
        df = df[['sku', 'name', 'category', 'current_stock', 'initial_stock', 
                'min_stock', 'max_stock', 'needs_reorder', 'sales_count', 
                'revenue', 'cost_price', 'sale_price', 'profit_margin']]
        
        # Rename columns for better readability
        df.columns = ['SKU', 'Product Name', 'Category', 'Current Stock', 'Initial Stock', 
                      'Min Stock', 'Max Stock', 'Needs Reorder', 'Sales Count', 
                      'Revenue (₵)', 'Cost Price (₵)', 'Sale Price (₵)', 'Profit Margin (%)']
        
        # Format currency columns
        for col in ['Revenue (₵)', 'Cost Price (₵)', 'Sale Price (₵)']:
            df[col] = df[col].apply(lambda x: f"{x:.2f}")
        
        # Format percentage column
        df['Profit Margin (%)'] = df['Profit Margin (%)'].apply(lambda x: f"{x:.2f}")
        
        # Create Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Low Stock Report', index=False)
            
            # Get workbook and worksheet objects
            workbook = writer.book
            worksheet = writer.sheets['Low Stock Report']
            
            # Add formats
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D7E4BC',
                'border': 1
            })
            
            # Add currency format
            currency_format = workbook.add_format({'num_format': '₵#,##0.00'})
            
            # Apply header format
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Set column widths
            worksheet.set_column('A:A', 10)  # SKU
            worksheet.set_column('B:B', 30)  # Product Name
            worksheet.set_column('C:C', 15)  # Category
            worksheet.set_column('D:G', 12)  # Stock columns
            worksheet.set_column('H:H', 15)  # Needs Reorder
            worksheet.set_column('I:I', 12)  # Sales Count
            worksheet.set_column('J:L', 15)  # Revenue, Cost, Sale Price
            worksheet.set_column('M:M', 15)  # Profit Margin
            
            # Add conditional formatting for low stock
            red_format = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
            yellow_format = workbook.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C6500'})
            green_format = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
            
            # Apply conditional formatting to Current Stock column (D)
            worksheet.conditional_format('D2:D1000', {'type': 'cell', 'criteria': '==', 'value': 0, 'format': red_format})
            worksheet.conditional_format('D2:D1000', {'type': 'cell', 'criteria': 'between', 'minimum': 1, 'maximum': 4, 'format': yellow_format})
            worksheet.conditional_format('D2:D1000', {'type': 'cell', 'criteria': '>=', 'value': 5, 'format': green_format})
            
            # Add title and date
            title_format = workbook.add_format({'bold': True, 'font_size': 16})
            date_format = workbook.add_format({'bold': True, 'font_size': 12})
            
            # Insert rows at the top
            worksheet.write('A1', 'Low Stock Report', title_format)
            worksheet.write('A2', f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', date_format)
            
            # Move the actual data down
            worksheet.write('A4', 'SKU', header_format)
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(3, col_num, value, header_format)
        
        # Set up response
        output.seek(0)
        
        # Generate filename with date
        filename = f"low_stock_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        import traceback
        print(f"Error generating low stock report: {str(e)}")
        print(traceback.format_exc())
        flash(f'Error generating report: {str(e)}', 'danger')
        return redirect(url_for('inventory.products'))

# API endpoint for low stock count
@inventory.route('/api/low-stock-count')
@login_required
def api_low_stock_count():
    """API endpoint for low stock count"""
    low_stock_count = Product.query.filter(
        Product.qty_available <= Product.min_qty,
        Product.active == True
    ).count()
    
    return jsonify({'count': low_stock_count})

# Warehouses and Locations
@inventory.route('/warehouses')
@login_required
def warehouses():
    warehouses = Warehouse.query.all()
    return render_template('inventory/warehouses.html', warehouses=warehouses)

@inventory.route('/warehouses/<int:warehouse_id>')
@login_required
def view_warehouse(warehouse_id):
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    locations = StockLocation.query.filter_by(warehouse_id=warehouse_id).all()
    return render_template('inventory/view_warehouse.html', warehouse=warehouse, locations=locations)

@inventory.route('/warehouses/new', methods=['GET', 'POST'])
@login_required
def new_warehouse():
    form = WarehouseForm()
    
    if form.validate_on_submit():
        warehouse = Warehouse(
            name=form.name.data,
            code=form.code.data,
            address=form.address.data
        )
        
        db.session.add(warehouse)
        db.session.commit()
        
        # Create default locations for the warehouse
        default_locations = [
            StockLocation(name='Stock', warehouse_id=warehouse.id, location_type='internal'),
            StockLocation(name='Input', warehouse_id=warehouse.id, location_type='input'),
            StockLocation(name='Output', warehouse_id=warehouse.id, location_type='output'),
            StockLocation(name='Quality Control', warehouse_id=warehouse.id, location_type='internal'),
            StockLocation(name='Scrap', warehouse_id=warehouse.id, location_type='inventory_loss')
        ]
        
        db.session.add_all(default_locations)
        db.session.commit()
        
        flash('Warehouse created successfully!', 'success')
        return redirect(url_for('inventory.warehouses'))
    
    return render_template('inventory/warehouse_form.html', form=form, title='New Warehouse')

@inventory.route('/warehouses/<int:warehouse_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_warehouse(warehouse_id):
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    form = WarehouseForm(obj=warehouse)
    
    if form.validate_on_submit():
        warehouse.name = form.name.data
        warehouse.code = form.code.data
        warehouse.address = form.address.data
        
        db.session.commit()
        flash('Warehouse updated successfully', 'success')
        return redirect(url_for('inventory.view_warehouse', warehouse_id=warehouse.id))
    
    return render_template('inventory/edit_warehouse.html', form=form, warehouse=warehouse)

@inventory.route('/warehouses/<int:warehouse_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_warehouse(warehouse_id):
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    
    # Check if warehouse has any stock locations
    locations = StockLocation.query.filter_by(warehouse_id=warehouse_id).all()
    if locations:
        flash('Cannot delete warehouse that has stock locations. Delete the locations first.', 'danger')
        return redirect(url_for('inventory.view_warehouse', warehouse_id=warehouse_id))
    
    db.session.delete(warehouse)
    db.session.commit()
    
    flash('Warehouse deleted successfully', 'success')
    return redirect(url_for('inventory.warehouses'))

@inventory.route('/stock-locations')
@login_required
def stock_locations():
    stock_locations = StockLocation.query.all()
    return render_template('inventory/stock_locations.html', stock_locations=stock_locations)

@inventory.route('/stock-locations/new', methods=['GET', 'POST'])
@login_required
def new_stock_location():
    form = StockLocationForm()
    form.warehouse_id.choices = [(w.id, w.name) for w in Warehouse.query.all()]
    
    if form.validate_on_submit():
        location = StockLocation(
            name=form.name.data,
            code=form.code.data,
            warehouse_id=form.warehouse_id.data,
            usage=form.usage.data,
            location_type=form.location_type.data
        )
        
        db.session.add(location)
        db.session.commit()
        
        flash('Stock location created successfully!', 'success')
        return redirect(url_for('inventory.view_warehouse', warehouse_id=form.warehouse_id.data))
    
    return render_template('inventory/location_form.html', form=form, title='New Stock Location')

@inventory.route('/stock-locations/<int:location_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_location(location_id):
    location = StockLocation.query.get_or_404(location_id)
    form = StockLocationForm(obj=location)
    form.warehouse_id.choices = [(w.id, w.name) for w in Warehouse.query.all()]
    
    if form.validate_on_submit():
        location.name = form.name.data
        location.code = form.code.data
        location.warehouse_id = form.warehouse_id.data
        location.usage = form.usage.data
        location.location_type = form.location_type.data
        
        db.session.commit()
        flash('Stock location updated successfully!', 'success')
        return redirect(url_for('inventory.view_warehouse', warehouse_id=location.warehouse_id))
    
    return render_template('inventory/location_form.html', form=form, title='Edit Stock Location', location=location)

@inventory.route('/stock-locations/<int:location_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_location(location_id):
    location = StockLocation.query.get_or_404(location_id)
    
    # Check if location has any stock
    stock_moves = StockMove.query.filter(
        db.or_(
            StockMove.source_location_id == location_id,
            StockMove.destination_location_id == location_id
        )
    ).first()
    
    if stock_moves:
        flash('Cannot delete location that has stock movements. Transfer all stock to another location first.', 'danger')
        return redirect(url_for('inventory.view_warehouse', warehouse_id=location.warehouse_id))
    
    # Get warehouse_id before deletion for redirect
    warehouse_id = location.warehouse_id
    location_name = location.name
    
    # Delete the location
    db.session.delete(location)
    db.session.commit()
    
    flash(f'Stock location "{location_name}" has been deleted.', 'success')
    return redirect(url_for('inventory.view_warehouse', warehouse_id=warehouse_id))
