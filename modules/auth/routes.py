from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from modules.auth.models import User, Role, UserRole
from modules.auth.forms import LoginForm, RegistrationForm, UserForm
from datetime import datetime
from extensions import db

auth = Blueprint('auth', __name__, url_prefix='/auth')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Redirect sales workers to POS dashboard
        if current_user.has_role('Sales Worker'):
            return redirect(url_for('pos.index'))
        return redirect(url_for('custom_dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            user.last_login = datetime.utcnow()
            db.session.commit()
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                # Redirect sales workers to POS dashboard
                if user.has_role('Sales Worker'):
                    next_page = url_for('pos.index')
                else:
                    next_page = url_for('custom_dashboard')
            return redirect(next_page)
        flash('Invalid username or password', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('custom_dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            is_active=True,
            created_at=datetime.utcnow()
        )
        user.set_password(form.password.data)
        
        # Assign default role
        employee_role = Role.query.filter_by(name='Employee').first()
        if employee_role:
            user_role = UserRole(role_id=employee_role.id)
            user.user_roles.append(user_role)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@auth.route('/users')
@login_required
def users():
    # Check if user has admin or manager role
    if not (current_user.has_role('Admin') or current_user.has_role('Manager')):
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    return render_template('auth/users.html', users=users)

@auth.route('/users/new', methods=['GET', 'POST'])
@login_required
def new_user():
    # Check if user has admin role
    if not current_user.has_role('Admin'):
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    
    form = UserForm()
    roles = Role.query.all()
    form.roles.choices = [(role.id, role.name) for role in roles]
    
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            is_active=form.is_active.data,
            created_at=datetime.utcnow()
        )
        user.set_password(form.password.data)
        
        # Assign roles
        for role_id in form.roles.data:
            user_role = UserRole(role_id=role_id)
            user.user_roles.append(user_role)
        
        db.session.add(user)
        db.session.commit()
        
        flash('User created successfully!', 'success')
        return redirect(url_for('auth.users'))
    
    return render_template('auth/user_form.html', form=form, title='New User')

@auth.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    # Check if user has admin role
    if not current_user.has_role('Admin'):
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    roles = Role.query.all()
    form.roles.choices = [(role.id, role.name) for role in roles]
    
    if request.method == 'GET':
        form.roles.data = [role.id for role in user.roles]
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.is_active = form.is_active.data
        
        if form.password.data:
            user.set_password(form.password.data)
        
        # Update roles
        user.user_roles = []
        for role_id in form.roles.data:
            user_role = UserRole(role_id=role_id)
            user.user_roles.append(user_role)
        
        db.session.commit()
        
        flash('User updated successfully!', 'success')
        return redirect(url_for('auth.users'))
    
    return render_template('auth/user_form.html', form=form, user=user, title='Edit User')

@auth.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    # Check if user has admin role
    if not current_user.has_role('Admin'):
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('auth.users'))
    
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting self
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('auth.users'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash('User deleted successfully!', 'success')
    return redirect(url_for('auth.users'))

@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UserForm(obj=current_user)
    
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        
        if form.password.data:
            current_user.set_password(form.password.data)
        
        db.session.commit()
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile.html', form=form)
