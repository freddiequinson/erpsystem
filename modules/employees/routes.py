from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from sqlalchemy import func

from .models import Employee, Department, JobPosition, EmployeeDocument, Leave, LeaveType, LeaveAllocation, Attendance
from .forms import DepartmentForm, JobPositionForm, EmployeeForm, LeaveForm, LeaveTypeForm, AttendanceForm, UserAccountForm
from extensions import db
from modules.auth.models import User, Role, UserRole

employees_bp = Blueprint('employees', __name__, template_folder='templates')

@employees_bp.route('/')
@login_required
def index():
    """Display list of employees"""
    # Admin sees all employees
    # Branch managers see only employees from their branch
    if current_user.has_role('admin'):
        employees = Employee.query.all()
    else:
        # Regular users see all employees
        employees = Employee.query.all()
    
    return render_template('employees/index.html', employees=employees, title="Employees")

@employees_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_employee():
    form = EmployeeForm()
    
    # Populate dropdown fields
    # Show all users for everyone
    is_admin = current_user.has_role('admin')
    form.user_id.choices = [(0, 'None')] + [(u.id, u.username) for u in User.query.all()]
    
    form.department_id.choices = [(0, 'None')] + [(d.id, d.name) for d in Department.query.all()]
    form.job_position_id.choices = [(0, 'None')] + [(j.id, j.name) for j in JobPosition.query.all()]
    
    # Show all employees as potential managers
    form.manager_id.choices = [(0, 'None')] + [(e.id, e.full_name) for e in Employee.query.all()]
    
    if form.validate_on_submit():
        # Handle 0 values (None) for foreign keys
        department_id = form.department_id.data if form.department_id.data != 0 else None
        job_position_id = form.job_position_id.data if form.job_position_id.data != 0 else None
        manager_id = form.manager_id.data if form.manager_id.data != 0 else None
        user_id = form.user_id.data if form.user_id.data != 0 else None
        
        # If a user is selected, ensure it's valid
        if user_id:
            user = User.query.get(user_id)
            # No need to check branch_id as it's been removed
        
        employee = Employee(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            gender=form.gender.data,
            birth_date=form.birth_date.data,
            hire_date=form.hire_date.data,
            department_id=department_id,
            job_position_id=job_position_id,
            manager_id=manager_id,
            user_id=user_id,
            work_email=form.work_email.data,
            work_phone=form.work_phone.data,
            mobile_phone=form.mobile_phone.data,
            address=form.address.data,
            city=form.city.data,
            state=form.state.data,
            zip_code=form.zip_code.data,
            country=form.country.data,
            notes=form.notes.data,
            is_active=form.is_active.data
        )
        db.session.add(employee)
        db.session.commit()
        flash('Employee created successfully!', 'success')
        return redirect(url_for('employees.index'))
    return render_template('employees/employee_form.html', form=form, title="New Employee")

@employees_bp.route('/<int:employee_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    
    # Check if user has permission to edit this employee
    is_admin = current_user.has_role('admin')
    has_access = is_admin
    
    # If not admin, allow access to all employees
    if not is_admin:
        has_access = True
    
    if not has_access:
        flash('You do not have permission to edit this employee.', 'danger')
        return redirect(url_for('employees.index'))
    
    form = EmployeeForm(obj=employee)
    
    # Populate dropdown fields - show all options for everyone
    form.user_id.choices = [(0, 'None')] + [(u.id, u.username) for u in User.query.all()]
    form.manager_id.choices = [(0, 'None')] + [(e.id, e.full_name) for e in Employee.query.filter(Employee.id != employee_id).all()]
    form.department_id.choices = [(0, 'None')] + [(d.id, d.name) for d in Department.query.all()]
    form.job_position_id.choices = [(0, 'None')] + [(j.id, j.name) for j in JobPosition.query.all()]
    
    if form.validate_on_submit():
        # Handle 0 values (None) for foreign keys
        department_id = form.department_id.data if form.department_id.data != 0 else None
        job_position_id = form.job_position_id.data if form.job_position_id.data != 0 else None
        manager_id = form.manager_id.data if form.manager_id.data != 0 else None
        user_id = form.user_id.data if form.user_id.data != 0 else None
        
        employee.first_name = form.first_name.data
        employee.last_name = form.last_name.data
        employee.gender = form.gender.data
        employee.birth_date = form.birth_date.data
        employee.hire_date = form.hire_date.data
        employee.department_id = department_id
        employee.job_position_id = job_position_id
        employee.manager_id = manager_id
        employee.user_id = user_id
        employee.work_email = form.work_email.data
        employee.work_phone = form.work_phone.data
        employee.mobile_phone = form.mobile_phone.data
        employee.address = form.address.data
        employee.city = form.city.data
        employee.state = form.state.data
        employee.zip_code = form.zip_code.data
        employee.country = form.country.data
        employee.notes = form.notes.data
        employee.is_active = form.is_active.data
        db.session.commit()
        flash('Employee updated successfully!', 'success')
        return redirect(url_for('employees.view_employee', employee_id=employee.id))
    
    # Pre-select the current values
    if employee.user_id is None:
        form.user_id.data = 0
    if employee.department_id is None:
        form.department_id.data = 0
    if employee.job_position_id is None:
        form.job_position_id.data = 0
    if employee.manager_id is None:
        form.manager_id.data = 0
        
    return render_template('employees/employee_form.html', form=form, employee=employee, title="Edit Employee")

@employees_bp.route('/<int:employee_id>/delete')
@login_required
def delete_employee(employee_id):
    """Delete an employee"""
    employee = Employee.query.get_or_404(employee_id)
    
    # Store the name for the flash message
    employee_name = employee.full_name
    
    # Delete the employee
    db.session.delete(employee)
    db.session.commit()
    
    flash(f'Employee "{employee_name}" has been deleted successfully.', 'success')
    return redirect(url_for('employees.index'))

@employees_bp.route('/<int:employee_id>')
@login_required
def view_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    
    # All users can view all employees
    is_admin = current_user.has_role('admin')
    has_access = True
    
    if not has_access:
        flash('You do not have permission to view this employee.', 'danger')
        return redirect(url_for('employees.index'))
    
    # Get leave requests for this employee
    leaves = Leave.query.filter_by(employee_id=employee_id).order_by(Leave.start_date.desc()).limit(5).all()
    
    # Get attendance records for this employee
    attendances = Attendance.query.filter_by(employee_id=employee_id).order_by(Attendance.check_in.desc()).limit(5).all()
    
    # Get documents for this employee
    documents = EmployeeDocument.query.filter_by(employee_id=employee_id).all()
    
    return render_template('employees/view_employee.html', 
                           employee=employee, 
                           leaves=leaves, 
                           attendances=attendances,
                           documents=documents)

@employees_bp.route('/departments')
@login_required
def departments():
    departments = Department.query.all()
    return render_template('employees/departments.html', departments=departments, title="Departments")

@employees_bp.route('/departments/new', methods=['GET', 'POST'])
@login_required
def new_department():
    form = DepartmentForm()
    
    # Populate dropdown fields
    form.parent_id.choices = [(0, 'None')] + [(d.id, d.name) for d in Department.query.all()]
    
    # Filter managers based on branch for non-admin users
    is_admin = current_user.has_role('admin')
    if is_admin:
        form.manager_id.choices = [(0, 'None')] + [(e.id, e.full_name) for e in Employee.query.all()]
    else:
        # Get managers from the same branch
        managers = Employee.query.join(
            User, Employee.user_id == User.id
        ).filter(
            User.branch_id == current_user.branch_id
        ).all()
        form.manager_id.choices = [(0, 'None')] + [(e.id, e.full_name) for e in managers]
    
    if form.validate_on_submit():
        # Handle 0 values (None) for foreign keys
        parent_id = form.parent_id.data if form.parent_id.data != 0 else None
        manager_id = form.manager_id.data if form.manager_id.data != 0 else None
        
        department = Department(
            name=form.name.data,
            code=form.code.data,
            manager_id=manager_id,
            parent_id=parent_id,
            notes=form.notes.data,
            is_active=form.is_active.data
        )
        db.session.add(department)
        db.session.commit()
        flash('Department created successfully!', 'success')
        return redirect(url_for('employees.departments'))
    return render_template('employees/department_form.html', form=form, title="New Department")

@employees_bp.route('/departments/<int:department_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_department(department_id):
    department = Department.query.get_or_404(department_id)
    form = DepartmentForm(obj=department)
    
    # Populate dropdown fields
    form.parent_id.choices = [(0, 'None')] + [(d.id, d.name) for d in Department.query.filter(Department.id != department_id).all()]
    
    # Show all employees as potential managers
    form.manager_id.choices = [(0, 'None')] + [(e.id, e.full_name) for e in Employee.query.all()]
    
    if form.validate_on_submit():
        # Handle 0 values (None) for foreign keys
        parent_id = form.parent_id.data if form.parent_id.data != 0 else None
        manager_id = form.manager_id.data if form.manager_id.data != 0 else None
        
        department.name = form.name.data
        department.code = form.code.data
        department.manager_id = manager_id
        department.parent_id = parent_id
        department.notes = form.notes.data
        department.is_active = form.is_active.data
        db.session.commit()
        flash('Department updated successfully!', 'success')
        return redirect(url_for('employees.departments'))
    
    # Pre-select the current values
    if department.parent_id is None:
        form.parent_id.data = 0
    if department.manager_id is None:
        form.manager_id.data = 0
        
    return render_template('employees/department_form.html', form=form, department=department, title="Edit Department")

@employees_bp.route('/job-positions')
@login_required
def job_positions():
    job_positions = JobPosition.query.all()
    return render_template('employees/job_positions.html', job_positions=job_positions, title="Job Positions")

@employees_bp.route('/job-positions/new', methods=['GET', 'POST'])
@login_required
def new_job_position():
    form = JobPositionForm()
    
    # Populate dropdown fields
    form.department_id.choices = [(0, 'None')] + [(d.id, d.name) for d in Department.query.all()]
    
    # Filter managers based on branch for non-admin users
    is_admin = current_user.has_role('admin')
    if is_admin:
        form.manager_id.choices = [(0, 'None')] + [(e.id, e.full_name) for e in Employee.query.all()]
    else:
        # Get managers from the same branch
        managers = Employee.query.join(
            User, Employee.user_id == User.id
        ).filter(
            User.branch_id == current_user.branch_id
        ).all()
        form.manager_id.choices = [(0, 'None')] + [(e.id, e.full_name) for e in managers]
    
    if form.validate_on_submit():
        # Handle 0 values (None) for foreign keys
        department_id = form.department_id.data if form.department_id.data != 0 else None
        manager_id = form.manager_id.data if form.manager_id.data != 0 else None
        
        job_position = JobPosition(
            name=form.name.data,
            department_id=department_id,
            manager_id=manager_id,
            description=form.description.data,
            requirements=form.requirements.data,
            is_active=form.is_active.data
        )
        db.session.add(job_position)
        db.session.commit()
        flash('Job Position created successfully!', 'success')
        return redirect(url_for('employees.job_positions'))
    return render_template('employees/job_position_form.html', form=form, title="New Job Position")

@employees_bp.route('/job-positions/<int:job_position_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_job_position(job_position_id):
    job_position = JobPosition.query.get_or_404(job_position_id)
    form = JobPositionForm(obj=job_position)
    
    # Populate dropdown fields
    form.department_id.choices = [(0, 'None')] + [(d.id, d.name) for d in Department.query.all()]
    
    # Show all employees as potential managers
    form.manager_id.choices = [(0, 'None')] + [(e.id, e.full_name) for e in Employee.query.all()]
    
    if form.validate_on_submit():
        # Handle 0 values (None) for foreign keys
        department_id = form.department_id.data if form.department_id.data != 0 else None
        manager_id = form.manager_id.data if form.manager_id.data != 0 else None
        
        job_position.name = form.name.data
        job_position.department_id = department_id
        job_position.manager_id = manager_id
        job_position.description = form.description.data
        job_position.requirements = form.requirements.data
        job_position.is_active = form.is_active.data
        db.session.commit()
        flash('Job Position updated successfully!', 'success')
        return redirect(url_for('employees.job_positions'))
    
    # Pre-select the current values
    if job_position.department_id is None:
        form.department_id.data = 0
    if job_position.manager_id is None:
        form.manager_id.data = 0
        
    return render_template('employees/job_position_form.html', form=form, job_position=job_position, title="Edit Job Position")

@employees_bp.route('/job-positions/<int:job_position_id>/delete')
@login_required
def delete_job_position(job_position_id):
    job_position = JobPosition.query.get_or_404(job_position_id)
    
    # Check if the job position is being used by any employees
    employees_using_position = Employee.query.filter_by(job_position_id=job_position_id).count()
    
    if employees_using_position > 0:
        flash(f'Cannot delete job position "{job_position.name}" because it is assigned to {employees_using_position} employee(s).', 'danger')
    else:
        position_name = job_position.name
        db.session.delete(job_position)
        db.session.commit()
        flash(f'Job position "{position_name}" deleted successfully!', 'success')
    
    return redirect(url_for('employees.job_positions'))

@employees_bp.route('/leaves')
@login_required
def leaves():
    leaves = Leave.query.all()
    leave_types = LeaveType.query.all()
    return render_template('employees/leaves.html', leaves=leaves, leave_types=leave_types, title="Leave Management")

@employees_bp.route('/leaves/new', methods=['GET', 'POST'])
@login_required
def new_leave():
    form = LeaveForm()
    if form.validate_on_submit():
        leave = Leave(
            employee_id=form.employee_id.data,
            leave_type_id=form.leave_type_id.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            reason=form.reason.data,
            state='submitted'
        )
        # Calculate duration in days
        delta = leave.end_date - leave.start_date
        leave.duration = delta.days + 1
        
        db.session.add(leave)
        db.session.commit()
        flash('Leave request submitted successfully!', 'success')
        return redirect(url_for('employees.leaves'))
    return render_template('employees/leave_form.html', form=form, title="New Leave Request")

@employees_bp.route('/leaves/types/new', methods=['GET', 'POST'])
@login_required
def new_leave_type():
    form = LeaveTypeForm()
    if form.validate_on_submit():
        leave_type = LeaveType(
            name=form.name.data,
            code=form.code.data,
            allocation_type=form.allocation_type.data,
            max_days=form.max_days.data,
            requires_approval=form.requires_approval.data,
            is_paid=form.is_paid.data,
            color=form.color.data,
            is_active=form.is_active.data
        )
        db.session.add(leave_type)
        db.session.commit()
        flash('Leave Type created successfully!', 'success')
        return redirect(url_for('employees.leaves'))
    return render_template('employees/leave_type_form.html', form=form, title="New Leave Type")

@employees_bp.route('/leaves/<int:leave_id>/approve')
@login_required
def approve_leave(leave_id):
    leave = Leave.query.get_or_404(leave_id)
    leave.state = 'approved'
    db.session.commit()
    flash('Leave request approved!', 'success')
    return redirect(url_for('employees.leaves'))

@employees_bp.route('/leaves/<int:leave_id>/reject')
@login_required
def reject_leave(leave_id):
    leave = Leave.query.get_or_404(leave_id)
    leave.state = 'rejected'
    db.session.commit()
    flash('Leave request rejected!', 'success')
    return redirect(url_for('employees.leaves'))

@employees_bp.route('/attendances')
@login_required
def attendances():
    # Get filter dates from request
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    # Default to current month if no dates provided
    if not start_date_str:
        today = date.today()
        start_date = date(today.year, today.month, 1)
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        
    if not end_date_str:
        today = date.today()
        # Last day of current month
        next_month = today.replace(day=28) + timedelta(days=4)
        end_date = next_month - timedelta(days=next_month.day)
    else:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    
    # Get attendance records for the date range
    attendances = Attendance.query.filter(
        func.date(Attendance.check_in) >= start_date,
        func.date(Attendance.check_in) <= end_date
    ).order_by(Attendance.check_in.desc()).all()
    
    # Get today's attendance
    today = date.today()
    today_attendances = Attendance.query.filter(
        func.date(Attendance.check_in) == today
    ).all()
    
    # Count present, absent, on leave
    present_count = len(today_attendances)
    
    # Count employees on leave today
    on_leave_count = Leave.query.filter(
        Leave.start_date <= today,
        Leave.end_date >= today,
        Leave.state == 'approved'
    ).count()
    
    # Total active employees
    total_employees = Employee.query.filter_by(is_active=True).count()
    
    # Absent = Total - (Present + On Leave)
    absent_count = total_employees - (present_count + on_leave_count)
    if absent_count < 0:
        absent_count = 0
    
    return render_template(
        'employees/attendances.html',
        attendances=attendances,
        today_attendances=today_attendances,
        present_count=present_count,
        on_leave_count=on_leave_count,
        absent_count=absent_count,
        title="Attendance"
    )

@employees_bp.route('/check-in', methods=['GET', 'POST'])
@login_required
def check_in():
    # Find employee record for current user
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    
    if not employee:
        flash('You do not have an employee record!', 'danger')
        return redirect(url_for('employees.attendances'))
    
    # Check if already checked in today
    today = date.today()
    existing_attendance = Attendance.query.filter(
        Attendance.employee_id == employee.id,
        func.date(Attendance.check_in) == today,
        Attendance.check_out.is_(None)
    ).first()
    
    if existing_attendance:
        flash('You are already checked in!', 'warning')
        return redirect(url_for('employees.attendances'))
    
    # Create new attendance record
    attendance = Attendance(
        employee_id=employee.id,
        check_in=datetime.now(),
        state='confirmed'
    )
    db.session.add(attendance)
    db.session.commit()
    
    flash('You have successfully checked in!', 'success')
    return redirect(url_for('employees.attendances'))

@employees_bp.route('/check-out')
@login_required
def check_out():
    # Find employee record for current user
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    
    if not employee:
        flash('You do not have an employee record!', 'danger')
        return redirect(url_for('employees.attendances'))
    
    # Find today's attendance record without checkout
    today = date.today()
    attendance = Attendance.query.filter(
        Attendance.employee_id == employee.id,
        func.date(Attendance.check_in) == today,
        Attendance.check_out.is_(None)
    ).first()
    
    if not attendance:
        flash('You have not checked in today!', 'warning')
        return redirect(url_for('employees.attendances'))
    
    # Update checkout time
    attendance.check_out = datetime.now()
    
    # Calculate worked hours
    delta = attendance.check_out - attendance.check_in
    attendance.worked_hours = delta.total_seconds() / 3600  # Convert seconds to hours
    
    db.session.commit()
    
    flash('You have successfully checked out!', 'success')
    return redirect(url_for('employees.attendances'))

@employees_bp.route('/<int:employee_id>/documents')
@login_required
def employee_documents(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    documents = EmployeeDocument.query.filter_by(employee_id=employee_id).all()
    return render_template('employees/documents.html', employee=employee, documents=documents, title=f"{employee.full_name} - Documents")

@employees_bp.route('/user-accounts')
@login_required
def user_accounts():
    users = User.query.all()
    return render_template('employees/user_accounts.html', users=users, title="User Accounts")

@employees_bp.route('/user-accounts/new', methods=['GET', 'POST'])
@login_required
def new_user_account():
    form = UserAccountForm()
    
    if form.validate_on_submit():
        # Check if username already exists
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Username already exists. Please choose a different username.', 'danger')
            return render_template('employees/user_account_form.html', form=form, title="New User Account")
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            is_active=form.is_active.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        # Assign role if selected
        if form.roles.data != 'none':
            role_name = None
            if form.roles.data == 'sales_worker':
                role_name = 'Sales Worker'
            elif form.roles.data == 'manager':
                role_name = 'Manager'
            elif form.roles.data == 'admin':
                role_name = 'Administrator'
            
            if role_name:
                # Check if role exists
                role = Role.query.filter_by(name=role_name).first()
                if not role:
                    # Create role if it doesn't exist
                    role = Role(name=role_name, description=f'{role_name} role')
                    db.session.add(role)
                    db.session.commit()
                
                # Assign role to user
                user_role = UserRole(user_id=user.id, role_id=role.id)
                db.session.add(user_role)
                db.session.commit()
        
        flash('User account created successfully!', 'success')
        return redirect(url_for('employees.user_accounts'))
    
    return render_template('employees/user_account_form.html', form=form, title="New User Account")

@employees_bp.route('/user-accounts/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user_account(user_id):
    user = User.query.get_or_404(user_id)
    form = UserAccountForm(obj=user)
    
    # Don't require password for existing users
    form.password.validators = []
    
    # Set the current role
    current_role = 'none'
    for role in user.roles:
        if role.name == 'Sales Worker':
            current_role = 'sales_worker'
        elif role.name == 'Manager':
            current_role = 'manager'
        elif role.name == 'Administrator':
            current_role = 'admin'
    
    form.roles.data = current_role
    
    if form.validate_on_submit():
        # Update user details
        user.username = form.username.data
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.is_active = form.is_active.data
        
        # Update password if provided
        if form.password.data:
            user.set_password(form.password.data)
        
        db.session.commit()
        
        # Update roles
        # First, remove all existing roles
        UserRole.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        
        # Then add the selected role
        if form.roles.data != 'none':
            role_name = None
            if form.roles.data == 'sales_worker':
                role_name = 'Sales Worker'
            elif form.roles.data == 'manager':
                role_name = 'Manager'
            elif form.roles.data == 'admin':
                role_name = 'Administrator'
            
            if role_name:
                # Check if role exists
                role = Role.query.filter_by(name=role_name).first()
                if not role:
                    # Create role if it doesn't exist
                    role = Role(name=role_name, description=f'{role_name} role')
                    db.session.add(role)
                    db.session.commit()
                
                # Assign role to user
                user_role = UserRole(user_id=user.id, role_id=role.id)
                db.session.add(user_role)
                db.session.commit()
        
        flash('User account updated successfully!', 'success')
        return redirect(url_for('employees.user_accounts'))
    
    return render_template('employees/user_account_form.html', form=form, user=user, title="Edit User Account")

@employees_bp.route('/employees/<int:employee_id>/create-user-account', methods=['GET', 'POST'])
@login_required
def create_employee_user_account(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    
    # Check if employee already has a user account
    if employee.user_id:
        flash('This employee already has a user account.', 'warning')
        return redirect(url_for('employees.view_employee', employee_id=employee_id))
    
    form = UserAccountForm()
    
    # Pre-fill form with employee data
    if not form.is_submitted():
        form.first_name.data = employee.first_name
        form.last_name.data = employee.last_name
        form.email.data = employee.work_email if employee.work_email else ''
    
    if form.validate_on_submit():
        # Check if username already exists
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Username already exists. Please choose a different username.', 'danger')
            return render_template('employees/user_account_form.html', form=form, employee=employee, title="Create User Account")
        
        # Check if email already exists
        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email:
            flash('Email already exists. Please use a different email address.', 'danger')
            return render_template('employees/user_account_form.html', form=form, employee=employee, title="Create User Account")
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            is_active=form.is_active.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        # Assign role if selected
        if form.roles.data != 'none':
            role_name = None
            if form.roles.data == 'sales_worker':
                role_name = 'Sales Worker'
            elif form.roles.data == 'manager':
                role_name = 'Manager'
            elif form.roles.data == 'admin':
                role_name = 'Administrator'
            
            if role_name:
                # Check if role exists
                role = Role.query.filter_by(name=role_name).first()
                if not role:
                    # Create role if it doesn't exist
                    role = Role(name=role_name, description=f'{role_name} role')
                    db.session.add(role)
                    db.session.commit()
                
                # Assign role to user
                user_role = UserRole(user_id=user.id, role_id=role.id)
                db.session.add(user_role)
                db.session.commit()
        
        # Link user to employee
        employee.user_id = user.id
        db.session.commit()
        
        flash('User account created and linked to employee successfully!', 'success')
        return redirect(url_for('employees.view_employee', employee_id=employee_id))
    
    return render_template('employees/user_account_form.html', form=form, employee=employee, title="Create User Account")
