from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, DateField, IntegerField, FloatField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Optional, Length, NumberRange

# ✅ CORRECT: Inherit from FlaskForm
class ProfileCompletionForm(FlaskForm):
    # Personal Information (All Roles)
    phone = StringField('Phone Number', validators=[DataRequired()])
    address = TextAreaField('Address', validators=[DataRequired(), Length(max=500)])
    location = StringField('City/State', validators=[DataRequired()])
    bio = TextAreaField('Bio/Description', validators=[DataRequired(), Length(max=1000)])
    profile_picture = FileField('Profile Picture', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    gender = SelectField('Gender', choices=[
        ('', 'Select Gender'),
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say')
    ], validators=[Optional()])

    # Farmer-specific fields
    farm_size = SelectField('Farm Size', choices=[
        ('small', 'Small (< 10 acres)'),
        ('medium', 'Medium (10-50 acres)'),
        ('large', 'Large (> 50 acres)')
    ], validators=[Optional()])
    crop_types = StringField('Crop Types (comma-separated)', validators=[Optional()])
    farming_method = SelectField('Farming Method', choices=[
        ('conventional', 'Conventional'),
        ('organic', 'Organic'),
        ('hydroponic', 'Hydroponic'),
        ('mixed', 'Mixed')
    ], validators=[Optional()])

    # Vendor-specific fields
    business_name = StringField('Business Name', validators=[Optional()])
    business_type = SelectField('Business Type', choices=[
        ('nursery', 'Nursery'),
        ('retailer', 'Retail Store'),
        ('wholesaler', 'Wholesaler'),
        ('distributor', 'Distributor')
    ], validators=[Optional()])
    vendor_type = SelectField('Vendor Type', choices=[
        ('wholesaler', 'Wholesaler'),
        ('retailer', 'Retailer'),
        ('exporter', 'Exporter'),
        ('importer', 'Importer')
    ], validators=[Optional()])
    product_categories = StringField('Product Categories (comma-separated)', validators=[Optional()])
    delivery_areas = TextAreaField('Delivery Areas', validators=[Optional()])

    # Consultant-specific fields
    expertise = StringField('Areas of Expertise (comma-separated)', validators=[Optional()])
    qualifications = TextAreaField('Qualifications', validators=[Optional()])
    experience_years = IntegerField('Years of Experience', validators=[Optional(), NumberRange(min=0, max=100)])
    consultation_fee = FloatField('Consultation Fee (per hour)', validators=[Optional(), NumberRange(min=0)])
    availability = SelectField('Availability', choices=[
        ('weekdays', 'Weekdays'),
        ('weekends', 'Weekends'),
        ('flexible', 'Flexible'),
        ('custom', 'Custom Schedule')
    ], validators=[Optional()])

    # Business Contact Information (for Farmers, Vendors, Consultants)
    business_description = TextAreaField('Business Description', validators=[Optional()])
    business_address = TextAreaField('Business Address', validators=[Optional()])
    business_phone = StringField('Business Phone', validators=[Optional()])
    business_website = StringField('Website (Optional)', validators=[Optional(), Length(max=200)])

    # Customer-specific fields
    interests = StringField('Agricultural Interests (comma-separated)', validators=[Optional()])
    preferred_contact = SelectField('Preferred Contact Method', choices=[
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('both', 'Both')
    ], validators=[Optional()])
    
    submit = SubmitField('Complete Profile')