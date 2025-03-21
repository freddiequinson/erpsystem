"""
This script updates the POS session functionality to:
1. Pre-select branch based on user's branch
2. Allow admin to select any branch
3. Pre-select cash register based on user's branch
4. Allow admin to select any cash register
"""
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import current_user
from extensions import db
from modules.pos.models import POSCashRegister, POSSession
from modules.auth.models import Branch

def update_pos_session_route():
    """
    Function to be copied into the POS module's routes.py file
    to replace the existing new_session function
    """
    @pos.route('/sessions/new', methods=['GET', 'POST'])
    @login_required
    def new_session():
        """Create a new POS session"""
        form = POSSessionForm()
        
        # Check if user is admin
        is_admin = current_user.has_role('admin')
        
        # Get all active branches
        branches = Branch.query.filter_by(is_active=True).all()
        
        # Set branch choices
        if is_admin:
            # Admin can select any branch
            form.branch_id.choices = [(b.id, b.name) for b in branches]
        else:
            # Non-admin users can only select their assigned branch
            user_branch_id = current_user.branch_id
            
            # If user has no branch_id, try to determine from username
            if not user_branch_id:
                username = current_user.username.lower()
                if 'branch' in username:
                    try:
                        branch_id = int(username.replace('branch', '').strip())
                        user_branch = Branch.query.get(branch_id)
                        if user_branch:
                            user_branch_id = user_branch.id
                    except (ValueError, AttributeError):
                        pass
                elif 'manager' in username:
                    try:
                        branch_id = int(username.replace('manager', '').strip())
                        user_branch = Branch.query.get(branch_id)
                        if user_branch:
                            user_branch_id = user_branch.id
                    except (ValueError, AttributeError):
                        pass
            
            # If we found a branch for the user, only show that branch
            if user_branch_id:
                user_branch = Branch.query.get(user_branch_id)
                if user_branch:
                    form.branch_id.choices = [(user_branch.id, user_branch.name)]
                else:
                    # Fallback to all branches if user's branch doesn't exist
                    form.branch_id.choices = [(b.id, b.name) for b in branches]
            else:
                # Fallback to all branches if we couldn't determine user's branch
                form.branch_id.choices = [(b.id, b.name) for b in branches]
        
        # Pre-select branch based on user's branch
        if request.method == 'GET':
            if not is_admin and current_user.branch_id:
                form.branch_id.data = current_user.branch_id
            elif not is_admin and len(form.branch_id.choices) == 1:
                # If only one branch is available, pre-select it
                form.branch_id.data = form.branch_id.choices[0][0]
            elif len(branches) > 0:
                # Default to first branch if no specific branch is assigned
                form.branch_id.data = branches[0].id
        
        # Handle branch selection change via AJAX or form submission
        selected_branch_id = request.form.get('branch_id', type=int)
        if not selected_branch_id and form.branch_id.data:
            selected_branch_id = form.branch_id.data
        
        # Filter cash registers by branch
        if is_admin:
            # Admin sees all cash registers for the selected branch
            if selected_branch_id:
                registers = POSCashRegister.query.filter_by(branch_id=selected_branch_id, is_active=True).all()
            else:
                registers = POSCashRegister.query.filter_by(is_active=True).all()
        else:
            # Branch managers and sales workers only see their branch's cash registers
            if current_user.branch_id:
                registers = POSCashRegister.query.filter_by(branch_id=current_user.branch_id, is_active=True).all()
            elif selected_branch_id:
                registers = POSCashRegister.query.filter_by(branch_id=selected_branch_id, is_active=True).all()
            else:
                registers = []
        
        if registers:
            # Set the choices for the dropdown
            form.cash_register_id.choices = [(r.id, r.name) for r in registers]
            
            # Pre-select the first register for non-admin users
            if request.method == 'GET' and not is_admin and len(registers) > 0:
                form.cash_register_id.data = registers[0].id
        else:
            flash(f'No cash registers found for the selected branch. Please contact an administrator.', 'warning')
            form.cash_register_id.choices = []
        
        if form.validate_on_submit():
            # Check if user already has an active session
            existing_session = POSSession.query.filter_by(user_id=current_user.id, end_time=None).first()
            if existing_session:
                flash('You already have an active POS session. Please close it before opening a new one.', 'warning')
                return redirect(url_for('pos.sessions'))
            
            # Create new session
            new_session = POSSession(
                user_id=current_user.id,
                cash_register_id=form.cash_register_id.data,
                branch_id=form.branch_id.data,
                opening_balance=form.opening_balance.data,
                notes=form.notes.data
            )
            
            try:
                db.session.add(new_session)
                db.session.commit()
                flash('POS session opened successfully!', 'success')
                return redirect(url_for('pos.terminal'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error opening session: {str(e)}', 'danger')
        
        return render_template('pos/session_form.html', 
                              title='Open POS Session',
                              form=form)

print("To implement these changes:")
print("1. Copy the updated new_session function from this file")
print("2. Replace the existing new_session function in modules/pos/routes.py")
print("3. Add JavaScript to handle dynamic branch/register selection in the session_form.html template")
