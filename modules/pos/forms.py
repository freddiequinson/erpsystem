from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, FloatField, BooleanField, SelectField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

class POSSessionForm(FlaskForm):
    cash_register_id = SelectField('Cash Register', coerce=int, validators=[DataRequired()])
    opening_balance = FloatField('Opening Balance', validators=[NumberRange(min=0)], default=0.0)
    closing_balance = FloatField('Closing Balance', validators=[Optional(), NumberRange(min=0)])
    notes = TextAreaField('Notes')
    submit = SubmitField('Submit')


class POSCashRegisterForm(FlaskForm):
    name = StringField('Register Name', validators=[DataRequired(), Length(1, 64)])
    balance = FloatField('Current Balance', validators=[NumberRange(min=0)], default=0.0)
    submit = SubmitField('Submit')


class POSCategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(1, 64)])
    parent_id = SelectField('Parent Category', coerce=int)
    sequence = IntegerField('Sequence', validators=[NumberRange(min=0)], default=10)
    image = FileField('Category Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField('Submit')


class POSPaymentMethodForm(FlaskForm):
    name = StringField('Method Name', validators=[DataRequired(), Length(1, 64)])
    code = StringField('Code', validators=[DataRequired(), Length(1, 20)])
    is_cash = BooleanField('Is Cash Method')
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Submit')


class POSDiscountForm(FlaskForm):
    name = StringField('Discount Name', validators=[DataRequired(), Length(1, 64)])
    discount_type = SelectField('Discount Type', choices=[
        ('percentage', 'Percentage (%)'),
        ('fixed', 'Fixed Amount (₵)')
    ], validators=[DataRequired()])
    value = FloatField('Value', validators=[DataRequired(), NumberRange(min=0)])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Submit')


class POSTaxForm(FlaskForm):
    name = StringField('Tax Name', validators=[DataRequired(), Length(1, 64)])
    rate = FloatField('Tax Rate (%)', validators=[DataRequired(), NumberRange(min=0, max=100)])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Submit')


class POSReceiptSettingsForm(FlaskForm):
    header_text = StringField('Header Text')
    footer_text = StringField('Footer Text')
    company_name = StringField('Company Name')
    company_address = StringField('Company Address')
    company_phone = StringField('Company Phone')
    company_logo = FileField('Company Logo', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    show_logo = BooleanField('Show Logo')
    show_cashier = BooleanField('Show Cashier Name')
    show_tax_details = BooleanField('Show Tax Details')
    show_barcode = BooleanField('Show Barcode')
    show_qr_code = BooleanField('Show QR Code')
    show_customer = BooleanField('Show Customer Details')
    submit = SubmitField('Save Settings')


class POSSettingsForm(FlaskForm):
    currency_symbol = StringField('Currency Symbol', validators=[DataRequired(), Length(1, 10)], default="₵")
    default_customer_id = SelectField('Default Customer', coerce=int, validators=[Optional()])
    allow_negative_stock = BooleanField('Allow Negative Stock', default=False)
    restrict_price_edit = BooleanField('Restrict Price Editing', default=True)
    auto_print_receipt = BooleanField('Auto-Print Receipt', default=True)
    submit = SubmitField('Save Settings')
    
    def __init__(self, *args, **kwargs):
        super(POSSettingsForm, self).__init__(*args, **kwargs)
        from modules.sales.models import Customer
        self.default_customer_id.choices = [(c.id, c.name) for c in Customer.query.all()]
        self.default_customer_id.choices.insert(0, (0, 'Walk-in Customer'))
