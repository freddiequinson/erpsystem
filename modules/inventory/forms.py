from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, FloatField, BooleanField, SelectField, SubmitField, DateTimeField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from datetime import datetime

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired(), Length(1, 128)])
    description = TextAreaField('Description')
    sku = StringField('SKU', validators=[Length(0, 64)])
    barcode = StringField('Barcode', validators=[Length(0, 64)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    uom_id = SelectField('Unit of Measure', coerce=int, validators=[DataRequired()])
    cost_price = FloatField('Cost Price', validators=[NumberRange(min=0)])
    sale_price = FloatField('Sale Price', validators=[NumberRange(min=0)])
    min_stock = FloatField('Minimum Stock', validators=[NumberRange(min=0)])
    max_stock = FloatField('Maximum Stock', validators=[NumberRange(min=0)])
    weight = FloatField('Weight', validators=[Optional(), NumberRange(min=0)])
    volume = FloatField('Volume', validators=[Optional(), NumberRange(min=0)])
    is_active = BooleanField('Active', default=True)
    image = FileField('Product Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField('Submit')


class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(1, 64)])
    description = TextAreaField('Description')
    parent_id = SelectField('Parent Category', coerce=int)
    submit = SubmitField('Submit')


class WarehouseForm(FlaskForm):
    name = StringField('Warehouse Name', validators=[DataRequired(), Length(1, 64)])
    code = StringField('Code', validators=[DataRequired(), Length(1, 10)])
    address = TextAreaField('Address')
    submit = SubmitField('Submit')


class StockLocationForm(FlaskForm):
    name = StringField('Location Name', validators=[DataRequired(), Length(1, 64)])
    code = StringField('Location Code', validators=[Length(0, 20)])
    warehouse_id = SelectField('Warehouse', coerce=int, validators=[DataRequired()])
    location_type = SelectField('Location Type', choices=[
        ('internal', 'Internal'),
        ('customer', 'Customer'),
        ('supplier', 'Supplier'),
        ('inventory_loss', 'Inventory Loss'),
        ('production', 'Production'),
        ('transit', 'Transit'),
        ('view', 'View')
    ])
    usage = TextAreaField('Usage Description', validators=[Optional()])
    submit = SubmitField('Submit')


class StockMoveForm(FlaskForm):
    product_id = SelectField('Product', coerce=int, validators=[DataRequired()])
    source_location_id = SelectField('Source Location', coerce=int, validators=[DataRequired()])
    destination_location_id = SelectField('Destination Location', coerce=int, validators=[DataRequired()])
    quantity = FloatField('Quantity', validators=[DataRequired(), NumberRange(min=0.01)])
    reference = StringField('Reference', validators=[Length(0, 64)])
    reference_type = SelectField('Reference Type', choices=[
        ('internal', 'Internal Transfer'),
        ('purchase', 'Purchase'),
        ('sale', 'Sale'),
        ('production', 'Production'),
        ('inventory', 'Inventory Adjustment')
    ])
    scheduled_date = DateTimeField('Scheduled Date', format='%Y-%m-%d %H:%M', default=datetime.utcnow)
    submit = SubmitField('Submit')


class InventoryForm(FlaskForm):
    name = StringField('Inventory Name', validators=[DataRequired(), Length(1, 64)])
    location_id = SelectField('Location', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit')


class UnitOfMeasureForm(FlaskForm):
    name = StringField('UOM Name', validators=[DataRequired(), Length(1, 64)])
    code = StringField('Code', validators=[DataRequired(), Length(1, 10)])
    category = SelectField('Category', choices=[
        ('unit', 'Unit'),
        ('weight', 'Weight'),
        ('volume', 'Volume'),
        ('length', 'Length'),
        ('time', 'Time')
    ])
    ratio = FloatField('Ratio', validators=[DataRequired(), NumberRange(min=0.000001)])
    submit = SubmitField('Submit')
