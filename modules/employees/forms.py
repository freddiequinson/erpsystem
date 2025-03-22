from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, FloatField, BooleanField, SelectField, SubmitField, DateField
from wtforms.validators import DataRequired, Length, Optional, Email, URL, NumberRange
from datetime import datetime, date

class DepartmentForm(FlaskForm):
    name = StringField('Department Name', validators=[DataRequired(), Length(1, 64)])
    code = StringField('Department Code', validators=[Optional(), Length(1, 20)])
    parent_id = SelectField('Parent Department', coerce=int)
    manager_id = SelectField('Department Manager', coerce=int)
    notes = TextAreaField('Notes')
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Submit')


class JobPositionForm(FlaskForm):
    name = StringField('Position Name', validators=[DataRequired(), Length(1, 64)])
    department_id = SelectField('Department', coerce=int)
    manager_id = SelectField('Position Manager', coerce=int)
    description = TextAreaField('Description')
    requirements = TextAreaField('Requirements')
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Submit')


class EmployeeForm(FlaskForm):
    user_id = SelectField('User Account', coerce=int)
    first_name = StringField('First Name', validators=[DataRequired(), Length(1, 64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(1, 64)])
    gender = SelectField('Gender', choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ])
    birth_date = DateField('Birth Date', validators=[Optional()], format='%Y-%m-%d')
    hire_date = DateField('Hire Date', validators=[DataRequired()], format='%Y-%m-%d', default=date.today)
    department_id = SelectField('Department', coerce=int)
    job_position_id = SelectField('Job Position', coerce=int)
    manager_id = SelectField('Manager', coerce=int)
    work_email = StringField('Work Email', validators=[Optional(), Length(0, 120), Email()])
    work_phone = StringField('Work Phone', validators=[Optional(), Length(0, 20)])
    mobile_phone = StringField('Mobile Phone', validators=[Optional(), Length(0, 20)])
    address = StringField('Address', validators=[Optional(), Length(0, 255)])
    city = StringField('City', validators=[Optional(), Length(0, 64)])
    state = StringField('State/Province', validators=[Optional(), Length(0, 64)])
    zip_code = StringField('ZIP/Postal Code', validators=[Optional(), Length(0, 20)])
    country = StringField('Country', validators=[Optional(), Length(0, 64)])
    notes = TextAreaField('Notes')
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Submit')


class EmployeeDocumentForm(FlaskForm):
    name = StringField('Document Name', validators=[DataRequired(), Length(1, 128)])
    document_type = SelectField('Document Type', choices=[
        ('id', 'Identification'),
        ('passport', 'Passport'),
        ('visa', 'Visa'),
        ('work_permit', 'Work Permit'),
        ('certificate', 'Certificate'),
        ('contract', 'Contract'),
        ('other', 'Other')
    ])
    document_file = FileField('Document File', validators=[
        FileAllowed(['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'], 'Only PDF, images, and Word documents are allowed!')
    ])
    issue_date = DateField('Issue Date', validators=[Optional()], format='%Y-%m-%d')
    expiry_date = DateField('Expiry Date', validators=[Optional()], format='%Y-%m-%d')
    notes = TextAreaField('Notes')
    submit = SubmitField('Submit')


class LeaveTypeForm(FlaskForm):
    name = StringField('Leave Type Name', validators=[DataRequired(), Length(1, 64)])
    code = StringField('Code', validators=[DataRequired(), Length(1, 20)])
    allocation_type = SelectField('Allocation Type', choices=[
        ('fixed', 'Fixed'),
        ('accrual', 'Accrual')
    ], default='fixed')
    max_days = FloatField('Maximum Days', validators=[NumberRange(min=0)], default=0.0)
    requires_approval = BooleanField('Requires Approval', default=True)
    is_paid = BooleanField('Paid Leave', default=True)
    color = StringField('Color', validators=[Optional(), Length(7, 7)], default='#3498db')
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Submit')


class LeaveForm(FlaskForm):
    employee_id = SelectField('Employee', coerce=int, validators=[DataRequired()])
    leave_type_id = SelectField('Leave Type', coerce=int, validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()], format='%Y-%m-%d')
    end_date = DateField('End Date', validators=[DataRequired()], format='%Y-%m-%d')
    reason = TextAreaField('Reason')
    submit = SubmitField('Submit')


class LeaveAllocationForm(FlaskForm):
    employee_id = SelectField('Employee', coerce=int, validators=[DataRequired()])
    leave_type_id = SelectField('Leave Type', coerce=int, validators=[DataRequired()])
    allocation_date = DateField('Allocation Date', validators=[DataRequired()], format='%Y-%m-%d', default=date.today)
    expiry_date = DateField('Expiry Date', validators=[Optional()], format='%Y-%m-%d')
    days_allocated = FloatField('Days Allocated', validators=[DataRequired(), NumberRange(min=0.5)], default=0.0)
    notes = TextAreaField('Notes')
    submit = SubmitField('Submit')


class AttendanceForm(FlaskForm):
    employee_id = SelectField('Employee', coerce=int, validators=[DataRequired()])
    check_in = DateField('Check In', validators=[DataRequired()], format='%Y-%m-%d %H:%M:%S')
    check_out = DateField('Check Out', validators=[Optional()], format='%Y-%m-%d %H:%M:%S')
    notes = TextAreaField('Notes')
    submit = SubmitField('Submit')


class UserAccountForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(1, 64)])
    email = StringField('Email', validators=[DataRequired(), Length(1, 120), Email()])
    password = StringField('Password', validators=[DataRequired(), Length(6, 64)])
    first_name = StringField('First Name', validators=[DataRequired(), Length(1, 64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(1, 64)])
    roles = SelectField('Role', choices=[
        ('none', 'No Special Role'),
        ('sales_worker', 'Sales Worker'),
        ('manager', 'Manager'),
        ('admin', 'Administrator')
    ], default='none')
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Submit')
