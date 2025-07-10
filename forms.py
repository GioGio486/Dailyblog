from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError
from models import User

class BaseForm(FlaskForm):
    content = TextAreaField('Content', validators=[DataRequired()])
    visibility = SelectField('Visibility', choices=[
        ('private', 'Private'), ('friends', 'Friends Only'), ('public', 'Public')
    ])

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=5)])
    confirm = PasswordField('Confirm Password', validators=[EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class PostForm(BaseForm): submit = SubmitField('Create Post')
class EditPostForm(BaseForm): submit = SubmitField('Update Post')
