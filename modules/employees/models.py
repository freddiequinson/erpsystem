from datetime import datetime
from app import db
from modules.auth.models import User

class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    code = db.Column(db.String(20), unique=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    manager_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    parent = db.relationship('Department', remote_side=[id], backref=db.backref('children', lazy='dynamic'))
    employees = db.relationship('Employee', backref='department', foreign_keys='Employee.department_id', lazy='dynamic')
    manager = db.relationship('Employee', backref='managed_department', foreign_keys=[manager_id])
    
    def __repr__(self):
        return f'<Department {self.name}>'


class JobPosition(db.Model):
    __tablename__ = 'job_positions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    description = db.Column(db.Text)
    requirements = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    department = db.relationship('Department', backref='job_positions')
    employees = db.relationship('Employee', backref='job_position', lazy='dynamic')
    
    def __repr__(self):
        return f'<JobPosition {self.name}>'


class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    gender = db.Column(db.String(10))
    birth_date = db.Column(db.Date)
    hire_date = db.Column(db.Date, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    job_position_id = db.Column(db.Integer, db.ForeignKey('job_positions.id'))
    manager_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    work_email = db.Column(db.String(120))
    work_phone = db.Column(db.String(20))
    mobile_phone = db.Column(db.String(20))
    address = db.Column(db.String(255))
    city = db.Column(db.String(64))
    state = db.Column(db.String(64))
    zip_code = db.Column(db.String(20))
    country = db.Column(db.String(64))
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='employee')
    manager = db.relationship('Employee', remote_side=[id], backref=db.backref('subordinates', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Employee {self.first_name} {self.last_name}>'
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def years_of_service(self):
        if not self.hire_date:
            return 0
        today = datetime.utcnow().date()
        return (today - self.hire_date).days // 365
        
    @property
    def total_sales(self):
        """Calculate the total sales amount for this employee"""
        from modules.pos.models import POSOrder
        
        if not hasattr(self, '_total_sales'):
            orders = POSOrder.query.filter_by(employee_id=self.id, state='paid').all()
            self._total_sales = sum(order.total_amount for order in orders)
        
        return self._total_sales
    
    @property
    def total_orders(self):
        """Count the total number of orders processed by this employee"""
        from modules.pos.models import POSOrder
        
        if not hasattr(self, '_total_orders'):
            self._total_orders = POSOrder.query.filter_by(employee_id=self.id, state='paid').count()
        
        return self._total_orders
    
    @property
    def average_sale(self):
        """Calculate the average sale amount for this employee"""
        if self.total_orders > 0:
            return self.total_sales / self.total_orders
        return 0


class EmployeeDocument(db.Model):
    __tablename__ = 'employee_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    document_type = db.Column(db.String(64))
    file_path = db.Column(db.String(255))
    issue_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    employee = db.relationship('Employee', backref='documents')
    
    def __repr__(self):
        return f'<EmployeeDocument {self.name}>'
    
    @property
    def is_expired(self):
        if not self.expiry_date:
            return False
        return self.expiry_date < datetime.utcnow().date()


class Leave(db.Model):
    __tablename__ = 'leaves'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    leave_type_id = db.Column(db.Integer, db.ForeignKey('leave_types.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    duration = db.Column(db.Float, nullable=False)  # in days
    reason = db.Column(db.Text)
    state = db.Column(db.String(20), default='draft')  # draft, submitted, approved, rejected, cancelled
    approved_by = db.Column(db.Integer, db.ForeignKey('employees.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    employee = db.relationship('Employee', foreign_keys=[employee_id], backref='leaves')
    leave_type = db.relationship('LeaveType', backref='leaves')
    approver = db.relationship('Employee', foreign_keys=[approved_by])
    
    def __repr__(self):
        return f'<Leave {self.id}: {self.employee_id} - {self.start_date} to {self.end_date}>'


class LeaveType(db.Model):
    __tablename__ = 'leave_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    code = db.Column(db.String(20), unique=True)
    allocation_type = db.Column(db.String(20), default='fixed')  # fixed, accrual
    max_days = db.Column(db.Float, default=0.0)
    requires_approval = db.Column(db.Boolean, default=True)
    is_paid = db.Column(db.Boolean, default=True)
    color = db.Column(db.String(7))  # hex color code
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<LeaveType {self.name}>'


class LeaveAllocation(db.Model):
    __tablename__ = 'leave_allocations'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    leave_type_id = db.Column(db.Integer, db.ForeignKey('leave_types.id'), nullable=False)
    allocation_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date)
    days_allocated = db.Column(db.Float, nullable=False)
    days_taken = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    employee = db.relationship('Employee', backref='leave_allocations')
    leave_type = db.relationship('LeaveType', backref='allocations')
    
    def __repr__(self):
        return f'<LeaveAllocation {self.id}: {self.employee_id} - {self.leave_type_id}>'
    
    @property
    def days_remaining(self):
        return self.days_allocated - self.days_taken
    
    @property
    def is_expired(self):
        if not self.expiry_date:
            return False
        return self.expiry_date < datetime.utcnow().date()


class Attendance(db.Model):
    __tablename__ = 'attendances'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    check_in = db.Column(db.DateTime, nullable=False)
    check_out = db.Column(db.DateTime)
    worked_hours = db.Column(db.Float)
    state = db.Column(db.String(20), default='draft')  # draft, confirmed, rejected
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    employee = db.relationship('Employee', backref='attendances')
    
    def __repr__(self):
        return f'<Attendance {self.id}: {self.employee_id} - {self.check_in}>'
    
    @property
    def duration(self):
        if not self.check_out:
            return 0
        delta = self.check_out - self.check_in
        return delta.total_seconds() / 3600  # Convert to hours
