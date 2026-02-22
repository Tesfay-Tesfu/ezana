from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SelectField, SelectMultipleField, DateField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange, URL
from flask_wtf.file import FileField, FileAllowed

class BookingForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=255)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired(), Length(max=50)])
    services = SelectMultipleField('Services', choices=[], validators=[DataRequired()])
    event_date = DateField('Event Date', validators=[Optional()])
    guest_count = IntegerField('Number of Guests', validators=[Optional(), NumberRange(min=1)])
    message = TextAreaField('Additional Information', validators=[Optional()])

class ReviewForm(FlaskForm):
    client_name = StringField('Your Name', validators=[DataRequired(), Length(max=255)])
    rating = SelectField('Rating', choices=[(5,'5 - Excellent'),(4,'4 - Good'),(3,'3 - Average'),(2,'2 - Poor'),(1,'1 - Terrible')], coerce=int)
    comment = TextAreaField('Your Review', validators=[DataRequired()])

class SubscribeForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])

class ServiceForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    subtitle = StringField('Subtitle')
    description = TextAreaField('Description')
    features = StringField('Features (comma separated)')
    box_color = StringField('Box Color', default='#2E8B57')
    image = FileField('Upload Image', validators=[FileAllowed(['jpg','png','jpeg','gif'], 'Images only!')])
    image_url = StringField('Or Image URL', validators=[Optional(), URL()])

class FAQForm(FlaskForm):
    question = StringField('Question', validators=[DataRequired()])
    answer = TextAreaField('Answer', validators=[DataRequired()])
    display_order = IntegerField('Display Order', default=0)

class UsefulLinkForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    url = StringField('URL', validators=[DataRequired(), URL()])
    icon = StringField('Icon Class')
    display_order = IntegerField('Display Order', default=0)

class AdminLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')

class HeroSlideForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=255)])
    subtitle = StringField('Subtitle', validators=[Length(max=255)])
    image_file = FileField('Upload Image', validators=[FileAllowed(['jpg','png','jpeg','gif'], 'Images only!')])
    image_url = StringField('Or Image URL', validators=[Optional(), URL()])
    button_text = StringField('Button Text', default='Book Now')
    button_link = StringField('Button Link', default='/booking')
    display_order = IntegerField('Display Order', default=0)
    is_active = BooleanField('Active', default=True)

class SocialMediaForm(FlaskForm):
    facebook = StringField('Facebook URL', validators=[Optional(), URL()])
    instagram = StringField('Instagram URL', validators=[Optional(), URL()])
    twitter = StringField('Twitter URL', validators=[Optional(), URL()])
    linkedin = StringField('LinkedIn URL', validators=[Optional(), URL()])
    youtube = StringField('YouTube URL', validators=[Optional(), URL()])
    tiktok = StringField('TikTok URL', validators=[Optional(), URL()])
