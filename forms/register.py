from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=100)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), Length(min=6), EqualTo('password', message='Passwords must match')])
    role = SelectField('Role', validators=[DataRequired()], 
                      choices=[('customer', 'Customer'), 
                              ('farmer', 'Farmer'),
                              ('vendor', 'Vendor'),
                              ('consultant', 'Agricultural Consultant')])
    submit = SubmitField('Register')