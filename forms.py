from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, SubmitField, TextAreaField, PasswordField
from wtforms.validators import DataRequired, Length

class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=50)])
    national_id = StringField('National ID', validators=[DataRequired(), Length(min=6, max=6)])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=10)])
    birth_date = DateField('Birthdate', format='%Y-%m-%d', validators=[DataRequired()])
    profession = SelectField('Profession', choices=[
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
        ('pharmacist', 'Pharmacist'),
        ('lab', 'Lab')
    ], validators=[DataRequired()])
    submit = SubmitField('Register')

class LabSubmissionForm(FlaskForm):
    patient_id = StringField('Patient ID', validators=[DataRequired()])
    test_type = StringField('Test Type', validators=[DataRequired(), Length(min=2, max=100)])
    result = TextAreaField('Test Result', validators=[DataRequired()])
    submit = SubmitField('Submit Test')
    # احذف حقل profession من الفورم
class LoginForm(FlaskForm):
    user_id = StringField('User ID', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=50)])
    submit = SubmitField('Login')