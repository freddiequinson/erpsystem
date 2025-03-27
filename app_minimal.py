"""
Minimal version of the ERP application for deployment.
This version excludes pandas-related functionality to ensure deployment works.
"""
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
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # Set up login manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
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
    
    # Register blueprints
    app.register_blueprint(auth)
    app.register_blueprint(inventory)
    app.register_blueprint(sales)
    app.register_blueprint(pos)
    app.register_blueprint(pos_api)
    app.register_blueprint(employees_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(purchase)
    app.register_blueprint(admin)
    app.register_blueprint(manager_bp)
    
    # Simple index route for testing
    @app.route('/')
    def index():
        return render_template('index.html')
    
    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500
    
    return app

if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    app.run(debug=True)
