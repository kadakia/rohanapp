from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from app.models import User
from flask_login import current_user

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username): # validate_<field_name> for custom validators
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()]) # why require this ?
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)]) # TextAreaFields are expandable
    submit = SubmitField('Submit')

    def validate_username(self, username): # validate_<field_name> for custom validators
        if current_user.username != username.data:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('This username is already taken.')

    #def __init__(self, original_username, *args, **kwargs):
    #    super(EditProfileForm, self).__init__(*args, **kwargs)
    #    self.original_username = original_username  ## original_username is given by current_user.username, an instance variable

    #def validate_username(self, username):
    #    if username.data != self.original_username:
    #        user = User.query.filter_by(username=self.username.data).first()
    #        if user is not None:
    #            raise ValidationError('This username is already taken.')

# enable account deletion

class PostForm(FlaskForm):
    post = TextAreaField('Say something:', validators=[DataRequired(), Length(min=1, max=140)])
    submit = SubmitField('Submit')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    # could alternatively ask for username
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')