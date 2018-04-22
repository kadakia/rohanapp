from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, ValidationError, Length
from app.models import User
from flask_login import current_user
from flask import request

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

class SearchForm(FlaskForm):
    q = StringField('Search Posts', validators=[DataRequired()])
    # no submit button, enter in order to submit
    # q.label.text = 'Search'

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args # default is request.form
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False # also, not putting form.hidden_tag() in the template
        super(SearchForm, self).__init__(*args, **kwargs)