from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, FloatField, BooleanField, PasswordField, FileField, SubmitField, URLField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional, NumberRange, URL as URLValidator

class LoginForm(FlaskForm):
    username = StringField('Username or Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    avatar = FileField('Avatar')
    submit = SubmitField('Update Profile')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

class MovieForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Optional()])
    category_id = SelectField('Category', coerce=int, validators=[Optional()])
    year = IntegerField('Year', validators=[Optional(), NumberRange(min=1900, max=2030)])
    duration = IntegerField('Duration (minutes)', validators=[Optional(), NumberRange(min=1)])
    rating = FloatField('Rating (0-10)', validators=[Optional(), NumberRange(min=0, max=10)])
    video_source_type = SelectField('Video Source', choices=[('upload', 'Upload File'), ('youtube', 'YouTube Link'), ('external', 'External Link')], default='upload')
    video_file = FileField('Video File')
    video_url = URLField('Video URL', validators=[Optional(), URLValidator()])
    cover_image = FileField('Cover Image', validators=[DataRequired()])
    submit = SubmitField('Post Movie')

class SeriesForm(FlaskForm):
    title = StringField('Series Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Optional()])
    category_id = SelectField('Category', coerce=int, validators=[Optional()])
    cover_image = FileField('Cover Image', validators=[DataRequired()])
    status = SelectField('Status', choices=[('ongoing', 'Ongoing'), ('completed', 'Completed')], default='ongoing')
    submit = SubmitField('Create Series')

class SeasonForm(FlaskForm):
    season_number = IntegerField('Season Number', validators=[DataRequired(), NumberRange(min=1)])
    title = StringField('Season Title', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Add Season')

class EpisodeForm(FlaskForm):
    title = StringField('Episode Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Optional()])
    episode_number = IntegerField('Episode Number', validators=[DataRequired(), NumberRange(min=1)])
    video_source_type = SelectField('Video Source', choices=[('upload', 'Upload File'), ('youtube', 'YouTube Link'), ('external', 'External Link')], default='upload')
    video_file = FileField('Video File')
    video_url = URLField('Video URL', validators=[Optional(), URLValidator()])
    thumbnail = FileField('Thumbnail', validators=[Optional()])
    duration = IntegerField('Duration (minutes)', validators=[Optional(), NumberRange(min=1)])
    submit = SubmitField('Add Episode')

class PlaylistForm(FlaskForm):
    name = StringField('Playlist Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    is_public = BooleanField('Make Public')
    submit = SubmitField('Create Playlist')

class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[DataRequired(), Length(min=1, max=2000)])
    submit = SubmitField('Post Comment')

class SearchForm(FlaskForm):
    query = StringField('Search', validators=[DataRequired()])
    category = SelectField('Category', coerce=int, validators=[Optional()])
    content_type = SelectField('Type', choices=[('', 'All'), ('movie', 'Movies'), ('series', 'Series')], default='')
    submit = SubmitField('Search')