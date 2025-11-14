# forms/consultant.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, FloatField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, NumberRange, Optional

class ConsultantRegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[Optional()])
    expertise = StringField('Area of Expertise', validators=[DataRequired()])
    experience_years = IntegerField('Years of Experience', 
                                   validators=[DataRequired(), NumberRange(min=0)])
    qualifications = TextAreaField('Qualifications & Certifications')
    consultation_fee = FloatField('Consultation Fee ($ per hour)', 
                                 validators=[NumberRange(min=0)])
    bio = TextAreaField('Professional Bio')
    availability = SelectField('Availability', choices=[
        ('weekdays', 'Weekdays'),
        ('weekends', 'Weekends'),
        ('flexible', 'Flexible'),
        ('by_appointment', 'By Appointment')
    ])
    submit = SubmitField('Register as Consultant')

class ConsultationRequestForm(FlaskForm):
    topic = StringField('Consultation Topic', validators=[DataRequired()])
    description = TextAreaField('Detailed Description', validators=[DataRequired()])
    consultation_type = SelectField('Consultation Type', choices=[
        ('general', 'General Advice'),
        ('crop_specific', 'Crop Specific'),
        ('pest_control', 'Pest & Disease Control'),
        ('soil_health', 'Soil Health'),
        ('business', 'Business Planning'),
        ('technical', 'Technical Guidance')
    ], validators=[DataRequired()])
    urgency = SelectField('Urgency Level', choices=[
        ('low', 'Low - General Inquiry'),
        ('medium', 'Medium - Need Advice Soon'),
        ('high', 'High - Urgent Issue')
    ])
    preferred_date = StringField('Preferred Date and Time')
    submit = SubmitField('Request Consultation')
