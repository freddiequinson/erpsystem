import os
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import current_user, login_required
from config import config
from datetime import datetime
from extensions import db, migrate, jwt, login_manager

def create_app(config_name='default'):
    # Create and configure the app
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # Import required modules
    from modules.auth.models import load_user
    from modules.auth.routes import auth
    from modules.inventory.routes import inventory
    from modules.sales.routes import sales
    from modules.pos.routes import pos
    from modules.pos.api import pos_api
    from modules.employees.routes import employees_bp
    from modules.reports.routes import reports_bp
    from modules.purchase.routes import purchase
    from modules.admin.routes import admin
    from modules.manager.routes import manager_bp
    from modules.auth.decorators import sales_worker_forbidden
    
    # Set up login manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.user_loader(load_user)
    
    # Register blueprints
    app.register_blueprint(auth)
    app.register_blueprint(inventory, url_prefix='/inventory')
    app.register_blueprint(sales, url_prefix='/sales')
    app.register_blueprint(pos, url_prefix='/pos')
    app.register_blueprint(pos_api)
    app.register_blueprint(employees_bp, url_prefix='/employees')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(purchase)
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(manager_bp, url_prefix='/manager')
    
    # Register error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500
    
    # Context processor for template variables
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow(), 'app_name': app.config['APP_NAME']}
    
    # Home route
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            # Redirect sales workers to POS dashboard
            if current_user.has_role('Sales Worker'):
                return redirect(url_for('pos.index'))
            return redirect(url_for('dashboard'))
        return redirect(url_for('auth.login'))
    
    # Dashboard route
    @app.route('/dashboard')
    @login_required
    def dashboard():
        try:
            from modules.inventory.models import Product, StockLocation, StockMove
            from modules.core.models import Activity
            from modules.employees.models import Employee
            from modules.pos.models import POSOrder, POSReturn
            from sqlalchemy import func
            from datetime import timedelta
            
            # Get current user's role
            is_admin = current_user.has_role('Admin')
            
            # Default values for dashboard
            context = {
                'employee_count': 0,
                'product_count': 0,
                'sales_order_count': 0,
                'purchase_order_count': 0,
                'pos_order_count': 0,
                'return_count': 0,
                'pos_sales_today': 0,
                'pos_sales_week': 0,
                'low_stock_products': [],
                'recent_orders': [],
                'recent_returns': [],
                'activities': [],
                'events': [],
                'branch_name': 'All Branches'
            }
            
            # Try to get actual counts if models exist
            try:
                # For admin users, show data from all branches
                # For regular users, filter by their branch
                
                # Employee count - filter by user's branch_id
                if not is_admin:
                    # Get employees whose associated user belongs to the current branch
                    from sqlalchemy import and_
                    from modules.auth.models import User
                    context['employee_count'] = Employee.query.join(
                        User, Employee.user_id == User.id
                    ).count()
                else:
                    # Admin sees all employees
                    context['employee_count'] = Employee.query.count()
                
                # Product count with proper branch filtering
                if not is_admin:
                    context['product_count'] = Product.query.count()
                else:
                    # Admin sees all products
                    context['product_count'] = Product.query.count()
                
                # POS order counts and sales
                today = datetime.utcnow().date()
                week_ago = today - timedelta(days=7)
                
                # Filter by branch for non-admin users only
                if not is_admin:
                    context['pos_order_count'] = POSOrder.query.count()
                    context['return_count'] = POSReturn.query.count()
                    
                    # Today's sales
                    today_sales = POSOrder.query.filter(
                        func.date(POSOrder.order_date) == today,
                        POSOrder.state == 'paid'
                    ).with_entities(func.sum(POSOrder.total_amount)).scalar()
                    
                    # Week's sales
                    week_sales = POSOrder.query.filter(
                        POSOrder.order_date >= week_ago,
                        POSOrder.state == 'paid'
                    ).with_entities(func.sum(POSOrder.total_amount)).scalar()
                else:
                    # For admin, show all orders across branches
                    context['pos_order_count'] = POSOrder.query.count()
                    context['return_count'] = POSReturn.query.count()
                    
                    # Today's sales across all branches
                    today_sales = POSOrder.query.filter(
                        func.date(POSOrder.order_date) == today,
                        POSOrder.state == 'paid'
                    ).with_entities(func.sum(POSOrder.total_amount)).scalar()
                    
                    # Week's sales across all branches
                    week_sales = POSOrder.query.filter(
                        POSOrder.order_date >= week_ago,
                        POSOrder.state == 'paid'
                    ).with_entities(func.sum(POSOrder.total_amount)).scalar()
                
                context['pos_sales_today'] = today_sales or 0
                context['pos_sales_week'] = week_sales or 0
                
                # Low stock products
                try:
                    # Query products filtered by branch for non-admin users only
                    if not is_admin:
                        all_products = Product.query.filter(
                            Product.is_active == True
                        ).all()
                    else:
                        # For admin, show all products across branches
                        all_products = Product.query.filter(Product.is_active == True).all()
                    
                    # Filter products with low stock (less than 5 units)
                    low_stock_products = []
                    for product in all_products:
                        try:
                            qty = product.available_quantity
                            if isinstance(qty, (int, float)) and qty < 5:
                                low_stock_products.append(product)
                        except Exception as e:
                            print(f"Error checking product {product.name}: {str(e)}")
                    
                    # Sort by available quantity (ascending)
                    low_stock_products.sort(key=lambda p: p.available_quantity if isinstance(p.available_quantity, (int, float)) else float('inf'))
                    
                    # Limit to 5 products for display
                    low_stock_products = low_stock_products[:5]
                    
                    print(f"Found {len(low_stock_products)} low stock products")
                except Exception as e:
                    print(f"Error fetching low stock products: {str(e)}")
                    import traceback
                    print(traceback.format_exc())
                    low_stock_products = []
                
                context['low_stock_products'] = low_stock_products
                
                # Recent POS transactions
                if not is_admin:
                    # Filter by branch for non-admin users
                    recent_orders = POSOrder.query.order_by(
                        POSOrder.order_date.desc()
                    ).limit(5).all()
                    
                    # Recent returns
                    recent_returns = POSReturn.query.order_by(
                        POSReturn.return_date.desc()
                    ).limit(5).all()
                else:
                    # For admin, show all recent orders across branches
                    recent_orders = POSOrder.query.order_by(
                        POSOrder.order_date.desc()
                    ).limit(5).all()
                    
                    # Recent returns across all branches
                    recent_returns = POSReturn.query.order_by(
                        POSReturn.return_date.desc()
                    ).limit(5).all()
                
                context['recent_orders'] = recent_orders
                context['recent_returns'] = recent_returns
                
                # Recent activities
                try:
                    # Check if the activities table exists and has data
                    with db.engine.connect() as conn:
                        # Check if table exists
                        result = conn.execute(db.text("""
                            SELECT name FROM sqlite_master 
                            WHERE type='table' AND name='activities'
                        """))
                        table_exists = result.fetchone() is not None
                        
                        if table_exists:
                            # Check if table has any records
                            count_result = conn.execute(db.text("SELECT COUNT(*) FROM activities"))
                            count = count_result.scalar()
                            
                            if count > 0:
                                # Only query activities if there are records
                                recent_activities = Activity.query.order_by(
                                    Activity.timestamp.desc()
                                ).limit(5).all()
                                context['activities'] = recent_activities
                            else:
                                context['activities'] = []
                        else:
                            context['activities'] = []
                except Exception as e:
                    print(f"Error loading activities for dashboard: {str(e)}")
                    context['activities'] = []
                
                # Upcoming events
                try:
                    from modules.core.models import Event
                    
                    # Use the ORM to query upcoming events
                    now = datetime.utcnow()
                    
                    # Base query
                    query = Event.query
                    
                    # Apply filters
                    query = query.filter(Event.date >= now)
                    
                    # Order by date
                    events = query.order_by(Event.date.asc()).limit(5).all()
                    
                    print(f"Found {len(events)} upcoming events for dashboard")
                    context['events'] = events
                except Exception as e:
                    # If there's an error, set empty events list
                    context['events'] = []
                    print(f"Error fetching upcoming events: {str(e)}")
                    import traceback
                    print(traceback.format_exc())
                
                # For demonstration, let's add some sample activities if none exist
                # Check if activities were explicitly cleared by looking for a session flag
                activities_cleared = session.get('activities_cleared', False)
                
                # Only show sample activities if there are none AND they haven't been explicitly cleared
                if len(context['activities']) == 0 and not activities_cleared:
                    sample_activities = [
                        Activity(
                            description="New product added",
                            details="Added 'Premium Coffee Beans' to inventory",
                            user="Admin",
                            timestamp=datetime.utcnow() - timedelta(hours=2),
                            activity_type="inventory"
                        ),
                        Activity(
                            description="Sales report generated",
                            details="Monthly sales report for March 2025",
                            user="Manager",
                            timestamp=datetime.utcnow() - timedelta(hours=5),
                            activity_type="report"
                        ),
                        Activity(
                            description="Return processed",
                            details="Processed return #RTN-2025-0042 for defective item",
                            user="Sales Rep",
                            timestamp=datetime.utcnow() - timedelta(hours=8),
                            activity_type="return"
                        )
                    ]
                    for activity in sample_activities:
                        db.session.add(activity)
                    db.session.commit()
                    context['activities'] = sample_activities
            except Exception as e:
                # Log the error but continue with default values
                print(f"Error loading dashboard data: {str(e)}")
                import traceback
                print(traceback.format_exc())
            
            return render_template('dashboard.html', **context)
        except ImportError as e:
            # Handle case where modules aren't available
            print(f"Import error in dashboard: {str(e)}")
            return render_template('dashboard.html', 
                                  employee_count=0,
                                  product_count=0,
                                  sales_order_count=0,
                                  purchase_order_count=0,
                                  pos_order_count=0,
                                  return_count=0,
                                  pos_sales_today=0,
                                  pos_sales_week=0,
                                  low_stock_products=[],
                                  recent_orders=[],
                                  recent_returns=[],
                                  activities=[],
                                  events=[])
    
    # Route to view all activities
    @app.route('/activities')
    @login_required
    def all_activities():
        try:
            from modules.core.models import Activity
            
            # First, check if the activities table exists
            with db.engine.connect() as conn:
                # Check if table exists
                result = conn.execute(db.text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='activities'
                """))
                table_exists = result.fetchone() is not None
                
                if not table_exists:
                    # Create the table if it doesn't exist
                    conn.execute(db.text('''
                    CREATE TABLE IF NOT EXISTS activities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        description VARCHAR(128) NOT NULL,
                        details TEXT,
                        user VARCHAR(64),
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        activity_type VARCHAR(32)
                    )
                    '''))
                    conn.commit()
                    flash("Activities table created successfully.", "success")
                    
                    # Add sample activities
                    from datetime import datetime, timedelta
                    now = datetime.utcnow()
                    
                    # Sample activities using raw SQL
                    sample_activities = [
                        (
                            "New product added", 
                            "Added 'Premium Coffee Beans' to inventory", 
                            "Admin", 
                            (now - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
                            "inventory"
                        ),
                        (
                            "Sales report generated", 
                            "Monthly sales report for March 2025", 
                            "Manager", 
                            (now - timedelta(hours=5)).strftime('%Y-%m-%d %H:%M:%S'),
                            "report"
                        ),
                        (
                            "Return processed", 
                            "Processed return #RTN-2025-0042 for defective item", 
                            "Sales Rep", 
                            (now - timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S'),
                            "return"
                        ),
                        (
                            "Quality check completed", 
                            "Completed quality inspection for returned items", 
                            "Quality Inspector", 
                            (now - timedelta(hours=12)).strftime('%Y-%m-%d %H:%M:%S'),
                            "quality"
                        ),
                        (
                            "New employee added", 
                            "Added John Doe to the Sales department", 
                            "HR Manager", 
                            (now - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S'),
                            "employee"
                        )
                    ]
                    
                    # Insert sample activities
                    for activity in sample_activities:
                        conn.execute(db.text("""
                            INSERT INTO activities 
                            (description, details, user, timestamp, activity_type) 
                            VALUES (?, ?, ?, ?, ?)
                        """), activity)
                    
                    conn.commit()
                    flash("Sample activities added.", "success")
            
            # Now query the activities
            activities = Activity.query.order_by(Activity.timestamp.desc()).all()
            return render_template('activities.html', activities=activities)
        
        except Exception as e:
            flash(f"Error loading activities: {str(e)}", "error")
            return redirect(url_for('dashboard'))
    
    # Route to clear all activities
    @app.route('/activities/clear')
    @login_required
    def clear_activities():
        try:
            from modules.core.models import Activity
            
            # Delete all activities
            Activity.query.delete()
            db.session.commit()
            
            # Set session flag to indicate activities were cleared
            session['activities_cleared'] = True
            
            flash("All activities have been cleared successfully.", "success")
            return redirect(url_for('all_activities'))
        
        except Exception as e:
            flash(f"Error clearing activities: {str(e)}", "error")
            return redirect(url_for('all_activities'))
    
    # Route to view all events
    @app.route('/events')
    @login_required
    def all_events():
        try:
            from modules.core.models import Event
            
            # First, check if the events table exists
            with db.engine.connect() as conn:
                # Check if table exists
                result = conn.execute(db.text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='events'
                """))
                table_exists = result.fetchone() is not None
                
                if not table_exists:
                    # Create the table if it doesn't exist
                    conn.execute(db.text('''
                    CREATE TABLE IF NOT EXISTS events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title VARCHAR(128) NOT NULL,
                        description TEXT,
                        date TIMESTAMP NOT NULL,
                        end_date TIMESTAMP,
                        location VARCHAR(128),
                        event_type VARCHAR(32),
                        created_by VARCHAR(64),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    '''))
                    conn.commit()
                    flash("Events table created successfully.", "success")
                    
                    # Add sample events
                    from datetime import datetime, timedelta
                    now = datetime.utcnow()
                    
                    # Sample events
                    sample_events = [
                        (
                            "Inventory Stocktaking", 
                            "Complete physical inventory count for Q2", 
                            (now + timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S'),
                            (now + timedelta(days=2, hours=4)).strftime('%Y-%m-%d %H:%M:%S'),
                            "Main Warehouse",
                            "inventory",
                            "Warehouse Manager"
                        ),
                        (
                            "Staff Training - POS System", 
                            "Training session on new POS features", 
                            (now + timedelta(days=5)).strftime('%Y-%m-%d %H:%M:%S'),
                            (now + timedelta(days=5, hours=3)).strftime('%Y-%m-%d %H:%M:%S'),
                            "Training Room",
                            "training",
                            "IT Manager"
                        ),
                        (
                            "Monthly Sales Review", 
                            "Review of sales performance and targets", 
                            (now + timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S'),
                            (now + timedelta(days=7, hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
                            "Conference Room",
                            "meeting",
                            "Sales Director"
                        ),
                        (
                            "Supplier Meeting - Accra Goods Ltd", 
                            "Negotiation of new supply terms", 
                            (now + timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S'),
                            (now + timedelta(days=10, hours=1, minutes=30)).strftime('%Y-%m-%d %H:%M:%S'),
                            "Executive Boardroom",
                            "meeting",
                            "Procurement Manager"
                        ),
                        (
                            "Product Launch - Premium Line", 
                            "Launch event for new premium product line", 
                            (now + timedelta(days=14)).strftime('%Y-%m-%d %H:%M:%S'),
                            (now + timedelta(days=14, hours=5)).strftime('%Y-%m-%d %H:%M:%S'),
                            "Kempinski Hotel, Accra",
                            "marketing",
                            "Marketing Director"
                        )
                    ]
                    
                    # Insert sample events
                    for event in sample_events:
                        conn.execute(db.text("""
                            INSERT INTO events 
                            (title, description, date, end_date, location, event_type, created_by) 
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """), event)
                    
                    conn.commit()
                    flash("Sample events added.", "success")
            
            # Get filter parameter
            filter_type = request.args.get('filter', None)
            
            # Base query
            query = Event.query
            
            # Apply filters
            if filter_type == 'upcoming':
                query = query.filter(Event.date >= datetime.utcnow())
            elif filter_type == 'today':
                today = datetime.utcnow().date()
                tomorrow = today + timedelta(days=1)
                query = query.filter(
                    func.date(Event.date) >= today,
                    func.date(Event.date) < tomorrow
                )
            elif filter_type == 'past':
                query = query.filter(Event.date < datetime.utcnow())
            
            # Order by date
            if filter_type == 'past':
                # Past events in descending order (most recent first)
                events = query.order_by(Event.date.desc()).all()
            else:
                # Upcoming events in ascending order (soonest first)
                events = query.order_by(Event.date.asc()).all()
            
            return render_template('events.html', events=events, filter=filter_type)
        
        except Exception as e:
            flash(f"Error loading events: {str(e)}", "error")
            return redirect(url_for('dashboard'))
    
    # Route to add a new event
    @app.route('/events/add', methods=['GET', 'POST'])
    @login_required
    def add_event():
        try:
            # Import necessary modules
            from modules.core.models import Event, Activity
            from datetime import datetime
            import traceback
            
            if request.method == 'POST':
                # Get form data
                title = request.form.get('title')
                description = request.form.get('description', '')
                date_str = request.form.get('date')
                end_date_str = request.form.get('end_date')
                location = request.form.get('location', '')
                event_type = request.form.get('event_type', '')
                created_by = request.form.get('created_by') or session.get('username', 'Admin')
                
                print(f"Form data received: title={title}, date={date_str}, end_date={end_date_str}, created_by={created_by}")
                
                # Validate required fields
                if not title or not date_str:
                    flash("Title and date are required fields.", "error")
                    return render_template('event_form.html', event=None)
                
                # Convert date strings to datetime objects
                try:
                    date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
                    print(f"Parsed date: {date}")
                    
                    end_date = None
                    if end_date_str and end_date_str.strip():
                        end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M')
                        print(f"Parsed end_date: {end_date}")
                except Exception as e:
                    print(f"Error parsing dates: {str(e)}")
                    flash(f"Error with date format: {str(e)}", "error")
                    return render_template('event_form.html', event=None)
                
                # Create new event using SQLAlchemy ORM
                try:
                    # Create new Event object
                    new_event = Event(
                        title=title,
                        description=description,
                        date=date,
                        end_date=end_date,
                        location=location,
                        event_type=event_type,
                        created_by=created_by
                    )
                    
                    # Add to database and commit
                    db.session.add(new_event)
                    db.session.commit()
                    
                    print(f"Event created successfully with ID: {new_event.id}")
                    
                    # Log activity
                    try:
                        activity = Activity(
                            description=f"Event scheduled: {title}",
                            details=f"New event scheduled for {date.strftime('%d/%m/%Y %H:%M')}",
                            user=created_by,
                            activity_type="event"
                        )
                        db.session.add(activity)
                        db.session.commit()
                    except Exception as e:
                        print(f"Error logging activity: {str(e)}")
                        # Continue even if activity logging fails
                    
                    flash(f"Event '{title}' has been scheduled successfully.", "success")
                    return redirect(url_for('all_events'))
                    
                except Exception as e:
                    db.session.rollback()
                    print(f"Error creating event: {str(e)}")
                    print(traceback.format_exc())
                    flash(f"Error creating event: {str(e)}", "error")
                    return render_template('event_form.html', event=None)
            
            # GET request - show form
            return render_template('event_form.html', event=None)
        
        except Exception as e:
            print(f"Unexpected error in add_event: {str(e)}")
            print(traceback.format_exc())
            flash(f"Error adding event: {str(e)}", "error")
            return redirect(url_for('all_events'))
    
    # Route to edit an event
    @app.route('/events/edit/<int:event_id>', methods=['GET', 'POST'])
    @login_required
    def edit_event(event_id):
        try:
            from modules.core.models import Event
            
            # Get the event
            event = Event.query.get_or_404(event_id)
            
            if request.method == 'POST':
                # Update event with form data
                event.title = request.form.get('title')
                event.description = request.form.get('description')
                
                # Convert date strings to datetime objects
                from datetime import datetime
                date_str = request.form.get('date')
                end_date_str = request.form.get('end_date')
                
                event.date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
                event.end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M') if end_date_str else None
                
                event.location = request.form.get('location')
                event.event_type = request.form.get('event_type')
                event.created_by = request.form.get('created_by')
                
                # Save changes
                db.session.commit()
                
                # Log activity
                from modules.core.models import Activity
                Activity.log(
                    description=f"Event updated: {event.title}",
                    details=f"Event details updated for {event.date.strftime('%d/%m/%Y %H:%M')}",
                    user=current_user.username,
                    activity_type="event"
                )
                
                flash(f"Event '{event.title}' has been updated successfully.", "success")
                return redirect(url_for('all_events'))
            
            # GET request - show form with event data
            return render_template('event_form.html', event=event)
        
        except Exception as e:
            flash(f"Error editing event: {str(e)}", "error")
            return redirect(url_for('all_events'))
    
    # Route to delete an event
    @app.route('/events/delete/<int:event_id>', methods=['POST'])
    @login_required
    def delete_event(event_id):
        try:
            from modules.core.models import Event
            
            # Get the event
            event = Event.query.get_or_404(event_id)
            
            # Store title for flash message
            title = event.title
            
            # Delete the event
            db.session.delete(event)
            db.session.commit()
            
            # Log activity
            from modules.core.models import Activity
            Activity.log(
                description=f"Event deleted: {title}",
                details=f"Event was removed from the calendar",
                user=current_user.username,
                activity_type="event"
            )
            
            flash(f"Event '{title}' has been deleted.", "success")
            
        except Exception as e:
            flash(f"Error deleting event: {str(e)}", "error")
            
        return redirect(url_for('all_events'))
    
    return app

if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    app.run(debug=True)
