from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, BooleanField, SelectField, SubmitField, DateTimeField
from wtforms.validators import DataRequired, Length, Optional, Email, URL, NumberRange
from datetime import datetime, timedelta

class SupplierForm(FlaskForm):
    name = StringField('Supplier Name', validators=[DataRequired(), Length(1, 128)])
    contact_name = StringField('Contact Name', validators=[Optional(), Length(0, 64)])
    email = StringField('Email', validators=[Optional(), Length(0, 120), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(0, 20)])
    address = StringField('Address', validators=[Optional(), Length(0, 255)])
    city = StringField('City', validators=[Optional(), Length(0, 64)])
    state = StringField('State/Province', validators=[Optional(), Length(0, 64)])
    zip_code = StringField('ZIP/Postal Code', validators=[Optional(), Length(0, 20)])
    country = StringField('Country', validators=[Optional(), Length(0, 64)])
    website = StringField('Website', validators=[Optional(), Length(0, 120), URL()])
    tax_id = StringField('Tax ID', validators=[Optional(), Length(0, 64)])
    notes = TextAreaField('Notes')
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Submit')


class PurchaseOrderForm(FlaskForm):
    supplier_id = SelectField('Supplier', coerce=int, validators=[DataRequired()])
    order_date = DateTimeField('Order Date', format='%Y-%m-%d', default=datetime.utcnow)
    expected_date = DateTimeField('Expected Date', format='%Y-%m-%d', default=lambda: datetime.utcnow() + timedelta(days=7))
    notes = TextAreaField('Notes')
    submit = SubmitField('Submit')


class PurchaseReceiptForm(FlaskForm):
    receipt_date = DateTimeField('Receipt Date', format='%Y-%m-%d', default=datetime.utcnow)
    notes = TextAreaField('Notes')
    submit = SubmitField('Submit')
    
    # Dynamic fields for line quantities will be added in the route


class PurchaseInvoiceForm(FlaskForm):
    invoice_date = DateTimeField('Invoice Date', format='%Y-%m-%d', default=datetime.utcnow)
    due_date = DateTimeField('Due Date', format='%Y-%m-%d', default=lambda: datetime.utcnow() + timedelta(days=30))
    notes = TextAreaField('Notes')
    submit = SubmitField('Submit')


class PurchasePaymentForm(FlaskForm):
    payment_date = DateTimeField('Payment Date', format='%Y-%m-%d', default=datetime.utcnow)
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    payment_method = SelectField('Payment Method', choices=[
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('other', 'Other')
    ])
    reference = StringField('Reference', validators=[Optional(), Length(0, 64)])
    notes = TextAreaField('Notes')
    submit = SubmitField('Submit')
