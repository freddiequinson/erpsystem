from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def role_required(*roles):
    """
    Decorator to restrict access to certain routes based on user roles.
    Usage: @role_required('Admin', 'Manager')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user has any of the required roles
            if not any(current_user.has_role(role) for role in roles):
                flash('You do not have permission to access this page.', 'danger')
                # Redirect to appropriate page based on role
                if current_user.has_role('Sales Worker'):
                    return redirect(url_for('pos.index'))
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def sales_worker_forbidden(f):
    """
    Decorator to restrict sales workers from accessing certain routes.
    Usage: @sales_worker_forbidden
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.has_role('Sales Worker'):
            flash('Sales workers do not have permission to access this page.', 'danger')
            return redirect(url_for('pos.index'))
        return f(*args, **kwargs)
    return decorated_function
