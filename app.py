import os
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import current_user, login_required
from config import config
from datetime import datetime
from extensions import db, migrate, jwt, login_manager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app(config_name='default'):
    # Create and configure the app
    app = Flask(__name__)
    
    # Log the configuration being used
    logger.info(f"Creating app with configuration: {config_name}")
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Log database connection info (safely)
    db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_url:
        # Only log the type of database, not the full connection string for security
        db_type = db_url.split('://')[0] if '://' in db_url else 'unknown'
        logger.info(f"Using database type: {db_type}")
    
    # Initialize extensions with app
    try:
        db.init_app(app)
        migrate.init_app(app, db)
        jwt.init_app(app)
        logger.info("Database and extensions initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing extensions: {str(e)}")
    
    # Import required modules
    try:
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
        logger.info("Modules imported successfully")
    except Exception as e:
        logger.error(f"Error importing modules: {str(e)}")
    
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
        try:
            # Redirect to custom login page
            return redirect(url_for('custom_login'))
        except Exception as e:
            # Log the error and return a simple error message
            logger.error(f"Error in index route: {str(e)}")
            return f"<h1>Enterprise ERP System</h1><p>Error: {str(e)}</p><a href='/custom-login'>Try Login</a>"
    
    # Dashboard route
    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Create a simplified dashboard page that doesn't rely on complex template variables
        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>ERP System Dashboard</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
            <style>
                .sidebar {
                    background-color: #343a40;
                    color: white;
                    min-height: 100vh;
                    padding-top: 20px;
                }
                .sidebar .nav-link {
                    color: rgba(255, 255, 255, 0.8);
                    padding: 10px 20px;
                    margin: 5px 0;
                }
                .sidebar .nav-link:hover {
                    color: white;
                    background-color: rgba(255, 255, 255, 0.1);
                }
                .sidebar .nav-link.active {
                    background-color: #007bff;
                    color: white;
                }
                .sidebar .nav-link i {
                    margin-right: 10px;
                }
                .card-dashboard {
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    margin-bottom: 20px;
                    transition: transform 0.3s;
                }
                .card-dashboard:hover {
                    transform: translateY(-5px);
                }
                .stat-card {
                    border-left: 5px solid;
                    border-radius: 5px;
                }
                .bg-gradient-primary {
                    background: linear-gradient(to right, #4e73df, #224abe);
                    color: white;
                }
                .bg-gradient-success {
                    background: linear-gradient(to right, #1cc88a, #13855c);
                    color: white;
                }
                .bg-gradient-info {
                    background: linear-gradient(to right, #36b9cc, #258391);
                    color: white;
                }
                .bg-gradient-warning {
                    background: linear-gradient(to right, #f6c23e, #dda20a);
                    color: white;
                }
            </style>
        </head>
        <body>
            <div class="container-fluid">
                <div class="row">
                    <!-- Sidebar -->
                    <div class="col-md-2 sidebar d-none d-md-block">
                        <h3 class="text-center mb-4">ERP System</h3>
                        <div class="nav flex-column">
                            <a href="/dashboard" class="nav-link active">
                                <i class="fas fa-tachometer-alt"></i> Dashboard
                            </a>
                            <a href="/inventory/products" class="nav-link">
                                <i class="fas fa-boxes"></i> Inventory
                            </a>
                            <a href="/sales" class="nav-link">
                                <i class="fas fa-chart-line"></i> Sales
                            </a>
                            <a href="/pos/index" class="nav-link">
                                <i class="fas fa-cash-register"></i> Point of Sale
                            </a>
                            <a href="/employees" class="nav-link">
                                <i class="fas fa-users"></i> Employees
                            </a>
                            <a href="/reports" class="nav-link">
                                <i class="fas fa-file-alt"></i> Reports
                            </a>
                            <a href="/auth/logout" class="nav-link mt-5">
                                <i class="fas fa-sign-out-alt"></i> Logout
                            </a>
                        </div>
                    </div>
                    
                    <!-- Main Content -->
                    <div class="col-md-10 ms-auto">
                        <div class="container mt-4">
                            <h1 class="mb-4">Dashboard</h1>
                            
                            <!-- Status Cards -->
                            <div class="row mb-4">
                                <div class="col-xl-3 col-md-6 mb-4">
                                    <div class="card card-dashboard bg-gradient-primary h-100">
                                        <div class="card-body">
                                            <div class="row no-gutters align-items-center">
                                                <div class="col mr-2">
                                                    <div class="text-xs font-weight-bold text-uppercase mb-1">Employees</div>
                                                    <div class="h5 mb-0 font-weight-bold">--</div>
                                                </div>
                                                <div class="col-auto">
                                                    <i class="fas fa-users fa-2x"></i>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="col-xl-3 col-md-6 mb-4">
                                    <div class="card card-dashboard bg-gradient-success h-100">
                                        <div class="card-body">
                                            <div class="row no-gutters align-items-center">
                                                <div class="col mr-2">
                                                    <div class="text-xs font-weight-bold text-uppercase mb-1">Products</div>
                                                    <div class="h5 mb-0 font-weight-bold">--</div>
                                                </div>
                                                <div class="col-auto">
                                                    <i class="fas fa-boxes fa-2x"></i>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="col-xl-3 col-md-6 mb-4">
                                    <div class="card card-dashboard bg-gradient-info h-100">
                                        <div class="card-body">
                                            <div class="row no-gutters align-items-center">
                                                <div class="col mr-2">
                                                    <div class="text-xs font-weight-bold text-uppercase mb-1">Today's Sales</div>
                                                    <div class="h5 mb-0 font-weight-bold">₵0.00</div>
                                                </div>
                                                <div class="col-auto">
                                                    <i class="fas fa-money-bill-wave fa-2x"></i>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="col-xl-3 col-md-6 mb-4">
                                    <div class="card card-dashboard bg-gradient-warning h-100">
                                        <div class="card-body">
                                            <div class="row no-gutters align-items-center">
                                                <div class="col mr-2">
                                                    <div class="text-xs font-weight-bold text-uppercase mb-1">Returns</div>
                                                    <div class="h5 mb-0 font-weight-bold">--</div>
                                                </div>
                                                <div class="col-auto">
                                                    <i class="fas fa-exchange-alt fa-2x"></i>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Main Content Cards -->
                            <div class="row">
                                <div class="col-lg-6 mb-4">
                                    <div class="card card-dashboard">
                                        <div class="card-header bg-light">
                                            <h5 class="m-0 font-weight-bold">Recent Activities</h5>
                                        </div>
                                        <div class="card-body">
                                            <p class="text-center text-muted py-5">No recent activities to display</p>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="col-lg-6 mb-4">
                                    <div class="card card-dashboard">
                                        <div class="card-header bg-light">
                                            <h5 class="m-0 font-weight-bold">Quick Actions</h5>
                                        </div>
                                        <div class="card-body">
                                            <div class="row">
                                                <div class="col-md-6 mb-3">
                                                    <a href="/pos/index" class="btn btn-primary btn-block w-100">
                                                        <i class="fas fa-cash-register me-2"></i> New Sale
                                                    </a>
                                                </div>
                                                <div class="col-md-6 mb-3">
                                                    <a href="/inventory/products/add" class="btn btn-success btn-block w-100">
                                                        <i class="fas fa-plus me-2"></i> Add Product
                                                    </a>
                                                </div>
                                                <div class="col-md-6 mb-3">
                                                    <a href="/reports" class="btn btn-info btn-block w-100">
                                                        <i class="fas fa-chart-bar me-2"></i> Sales Report
                                                    </a>
                                                </div>
                                                <div class="col-md-6 mb-3">
                                                    <a href="/custom-dashboard" class="btn btn-secondary btn-block w-100">
                                                        <i class="fas fa-tachometer-alt me-2"></i> Custom Dashboard
                                                    </a>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        </body>
        </html>
        '''
        return html
    
    # Database initialization route
    @app.route('/initialize-database')
    def initialize_database():
        try:
            # Create all tables
            db.create_all()
            logger.info("Database tables created successfully")
            
            # Check if admin user exists
            admin_user = User.query.filter_by(username='admin').first()
            if admin_user is None:
                # Create admin user
                admin_role = Role.query.filter_by(name='Admin').first()
                if admin_role is None:
                    admin_role = Role(name='Admin', description='Administrator')
                    db.session.add(admin_role)
                    logger.info("Admin role created")
                
                admin_user = User(
                    username='admin',
                    email='admin@example.com',
                    role=admin_role
                )
                admin_user.set_password('admin123')
                db.session.add(admin_user)
                db.session.commit()
                logger.info("Admin user created successfully")
                message = "Database initialized successfully. Admin user created with username 'admin' and password 'admin123'."
            else:
                logger.info("Admin user already exists")
                message = "Database initialized successfully. Admin user already exists."
            
            return f'''
            <html>
                <head>
                    <title>Database Initialized</title>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            margin: 0;
                            padding: 20px;
                            background-color: #f5f5f5;
                            text-align: center;
                        }}
                        .container {{
                            max-width: 800px;
                            margin: 0 auto;
                            background-color: white;
                            padding: 20px;
                            border-radius: 5px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        }}
                        h1 {{
                            color: #4CAF50;
                        }}
                        .message {{
                            margin: 20px 0;
                            padding: 10px;
                            background-color: #e8f5e9;
                            border-radius: 5px;
                        }}
                        .btn {{
                            display: inline-block;
                            padding: 10px 20px;
                            background-color: #4CAF50;
                            color: white;
                            text-decoration: none;
                            border-radius: 5px;
                            margin-top: 20px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>Database Initialization Complete</h1>
                        <div class="message">
                            {message}
                        </div>
                        <p>You can now proceed to the dashboard to start using the ERP system.</p>
                        <a href="/custom-dashboard" class="btn">Go to Dashboard</a>
                    </div>
                </body>
            </html>
            '''
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            error_message = str(e)
            return f'''
            <html>
                <head>
                    <title>Database Initialization Error</title>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            margin: 0;
                            padding: 20px;
                            background-color: #f5f5f5;
                            text-align: center;
                        }}
                        .container {{
                            max-width: 800px;
                            margin: 0 auto;
                            background-color: white;
                            padding: 20px;
                            border-radius: 5px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        }}
                        h1 {{
                            color: #f44336;
                        }}
                        .error {{
                            margin: 20px 0;
                            padding: 10px;
                            background-color: #ffebee;
                            border-radius: 5px;
                            color: #d32f2f;
                        }}
                        .btn {{
                            display: inline-block;
                            padding: 10px 20px;
                            background-color: #2196F3;
                            color: white;
                            text-decoration: none;
                            border-radius: 5px;
                            margin-top: 20px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>Database Initialization Error</h1>
                        <div class="error">
                            <p>An error occurred while initializing the database:</p>
                            <p>{error_message}</p>
                        </div>
                        <p>Please check your database configuration and try again.</p>
                        <a href="/custom-dashboard" class="btn">Return to Dashboard</a>
                    </div>
                </body>
            </html>
            '''
    
    # Custom login route that doesn't rely on the database
    @app.route('/custom-login', methods=['GET', 'POST'])
    def custom_login():
        error_message = None
        
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            if username == 'admin' and password == 'admin123':
                # Create a simple session without database
                session['logged_in'] = True
                session['username'] = username
                session['is_admin'] = True
                
                # Redirect to custom dashboard
                return redirect(url_for('custom_dashboard'))
            else:
                error_message = "Invalid username or password"
        
        # Return a simple login form
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>ERP System - Login</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    background-color: #f5f5f5;
                }}
                .login-container {{
                    background-color: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    width: 350px;
                }}
                h1 {{
                    text-align: center;
                    color: #333;
                    margin-bottom: 30px;
                }}
                .form-group {{
                    margin-bottom: 20px;
                }}
                label {{
                    display: block;
                    margin-bottom: 5px;
                    font-weight: bold;
                }}
                input[type="text"], input[type="password"] {{
                    width: 100%;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    box-sizing: border-box;
                }}
                .btn {{
                    display: block;
                    width: 100%;
                    padding: 10px;
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 16px;
                    text-align: center;
                }}
                .error {{
                    color: red;
                    margin-bottom: 15px;
                }}
                .info {{
                    margin-top: 20px;
                    text-align: center;
                    font-size: 14px;
                    color: #666;
                }}
                .db-link {{
                    display: block;
                    margin-top: 20px;
                    text-align: center;
                    color: #4CAF50;
                }}
            </style>
        </head>
        <body>
            <div class="login-container">
                <h1>ERP System Login</h1>
                {f'<p class="error">{error_message}</p>' if error_message else ''}
                <form method="POST">
                    <div class="form-group">
                        <label for="username">Username</label>
                        <input type="text" id="username" name="username" required>
                    </div>
                    <div class="form-group">
                        <label for="password">Password</label>
                        <input type="password" id="password" name="password" required>
                    </div>
                    <button type="submit" class="btn">Login</button>
                </form>
                <p class="info">Use username: <strong>admin</strong> and password: <strong>admin123</strong></p>
                <a href="/initialize-database" class="db-link">Initialize Database</a>
            </div>
        </body>
        </html>
        '''
        return html
        
    # Custom dashboard route
    @app.route('/custom-dashboard')
    @login_required
    def custom_dashboard():
        # Check if database has been initialized
        try:
            # Try to query the User table to check if database is initialized
            user_count = User.query.count()
            db_initialized = True
        except Exception as e:
            logger.error(f"Database not initialized: {str(e)}")
            db_initialized = False
        
        # Get username safely
        try:
            username = current_user.username
        except:
            username = "User"
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>ERP System Dashboard</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f5f5f5;
                }}
                .header {{
                    background-color: #333;
                    color: white;
                    padding: 15px 20px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .header h1 {{
                    margin: 0;
                }}
                .user-info {{
                    display: flex;
                    align-items: center;
                }}
                .logout-btn {{
                    color: white;
                    text-decoration: none;
                    margin-left: 15px;
                    padding: 5px 10px;
                    background-color: #d9534f;
                    border-radius: 3px;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 20px auto;
                    padding: 0 20px;
                }}
                .dashboard-card {{
                    background-color: white;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    padding: 20px;
                    margin-bottom: 20px;
                }}
                .card-title {{
                    margin-top: 0;
                    color: #333;
                    border-bottom: 1px solid #eee;
                    padding-bottom: 10px;
                }}
                .system-status {{
                    display: flex;
                    justify-content: space-around;
                    margin: 20px 0;
                }}
                .status-item {{
                    text-align: center;
                    padding: 15px;
                    border: 1px solid #eee;
                    border-radius: 5px;
                    width: 30%;
                }}
                .status-item h3 {{
                    margin-top: 0;
                }}
                .status-good {{
                    color: #4CAF50;
                }}
                .status-warning {{
                    color: #ff9800;
                }}
                .status-error {{
                    color: #f44336;
                }}
                .action-buttons {{
                    margin-top: 20px;
                    display: flex;
                    justify-content: center;
                    flex-wrap: wrap;
                }}
                .action-btn {{
                    display: inline-block;
                    padding: 10px 20px;
                    background-color: #4CAF50;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 10px;
                }}
                .menu-card {{
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: space-between;
                }}
                .menu-item {{
                    width: 30%;
                    margin-bottom: 20px;
                    padding: 15px;
                    background-color: #f9f9f9;
                    border-radius: 5px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }}
                .menu-item h3 {{
                    margin-top: 0;
                    color: #333;
                }}
                .menu-item p {{
                    color: #666;
                    margin-bottom: 15px;
                }}
                .menu-btn {{
                    display: inline-block;
                    padding: 8px 15px;
                    background-color: #2196F3;
                    color: white;
                    text-decoration: none;
                    border-radius: 3px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>ERP System Dashboard</h1>
                <div class="user-info">
                    <span>Welcome, {username}</span>
                    <a href="/auth/logout" class="logout-btn">Logout</a>
                </div>
            </div>
            
            <div class="container">
                <div class="dashboard-card">
                    <h2 class="card-title">System Status</h2>
                    <p>This is a simplified dashboard that provides access to key system functions. Use the options below to navigate your ERP system.</p>
                    
                    <div class="system-status">
                        <div class="status-item">
                            <h3>Database</h3>
                            <p class="{'status-good' if db_initialized else 'status-warning'}">{'Initialized' if db_initialized else 'Needs Initialization'}</p>
                        </div>
                        <div class="status-item">
                            <h3>Application</h3>
                            <p class="status-good">Running</p>
                        </div>
                        <div class="status-item">
                            <h3>User Authentication</h3>
                            <p class="status-good">Active</p>
                        </div>
                    </div>
                    
                    <div class="action-buttons">
                        <a href="/dashboard" class="action-btn">Original Dashboard</a>
                        {'<a href="/initialize-database" class="action-btn">Initialize Database</a>' if not db_initialized else ''}
                        <a href="/" class="action-btn">Home Page</a>
                        <a href="/auth/logout" class="action-btn">Logout</a>
                    </div>
                </div>
                
                <div class="dashboard-card">
                    <h2 class="card-title">System Navigation</h2>
                    
                    <div class="menu-card">
                        <div class="menu-item">
                            <h3>Inventory</h3>
                            <p>Manage products, stock levels, and locations</p>
                            <a href="/inventory/products" class="menu-btn">Products</a>
                        </div>
                        
                        <div class="menu-item">
                            <h3>Sales</h3>
                            <p>Manage orders, customers, and sales reports</p>
                            <a href="/pos/index" class="menu-btn">POS System</a>
                        </div>
                        
                        <div class="menu-item">
                            <h3>Users</h3>
                            <p>Manage system users and permissions</p>
                            <a href="/auth/users" class="menu-btn">Users</a>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''
        return html
        
    # Custom logout route
    @app.route('/custom-logout')
    def custom_logout():
        session.pop('logged_in', None)
        session.pop('username', None)
        session.pop('is_admin', None)
        return redirect(url_for('custom_login'))
    
    # Placeholder routes for dashboard links
    @app.route('/all-activities')
    @login_required
    def view_all_activities():
        return render_template('placeholder.html', title="All Activities", 
                              message="Activities functionality is coming soon.")
    
    @app.route('/all-events')
    @login_required
    def all_events():
        return render_template('placeholder.html', title="All Events", 
                              message="Events functionality is coming soon.")
    
    # Route to view all activities
    @app.route('/activities')
    @login_required
    def view_activities():
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
            return redirect(url_for('view_activities'))
        
        except Exception as e:
            flash(f"Error clearing activities: {str(e)}", "error")
            return redirect(url_for('view_activities'))
    
    # Route to view all events
    @app.route('/events')
    @login_required
    def view_all_events():
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
                    return redirect(url_for('view_all_events'))
                    
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
            return redirect(url_for('view_all_events'))
    
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
                return redirect(url_for('view_all_events'))
            
            # GET request - show form with event data
            return render_template('event_form.html', event=event)
        
        except Exception as e:
            flash(f"Error editing event: {str(e)}", "error")
            return redirect(url_for('view_all_events'))
    
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
            
        return redirect(url_for('view_all_events'))
    
    return app

if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    app.run(debug=True)
