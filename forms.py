from datetime import datetime
from flask_wtf import Form
from wtforms import StringField, SelectField, SelectMultipleField, DateTimeField, BooleanField
from wtforms.validators import DataRequired, AnyOf, URL
from enums import Genre, States
import re
import validators

class Meta:
    csrf = False

class ShowForm(Form):
    artist_id = StringField(
        'artist_id'
    )
    venue_id = StringField(
        'venue_id'
    )
    start_time = DateTimeField(
        'start_time',
        validators=[DataRequired()],
        default= datetime.today()
    )

class VenueForm(Form):
    name = StringField(
        'name', validators=[DataRequired()]
    )
    city = StringField(
        'city', validators=[DataRequired()]
    )
    state = SelectField(
        'state', validators=[DataRequired()],
        choices = States.choices
    )
    address = StringField(
        'address', validators=[DataRequired()]
    )
    phone = StringField(
        'phone'
    )
    image_link = StringField(
        'image_link'
    )
    genres = SelectMultipleField(
        'genres', validators=[DataRequired()],
        choices = Genre.choices()
    )
    facebook_link = StringField(
        'facebook_link'
    )
    website_link = StringField(
        'website_link'
    )

    seeking_talent = BooleanField( 'seeking_talent' )

    seeking_description = StringField(
        'seeking_description'
    )

    def validate(self): 
        def is_valid_phone(number):
            regex = re.compile('^\([0-9]{3}\) *[0-9]{3}-[0-9]{4}$|^[0-9]{3}-[0-9]{3}-[0-9]{4}$|^[0-9]{3}.[0-9]{3}.[0-9]{4}$|^$')
            return regex.match(number)

        def is_valid_facebook_link(facebookLink):
            # if valid or empty, count as valid
            if validators.url(facebookLink) or re.compile('^$').match(facebookLink):
                return True
            else: return False
        
        # perform default validation first
        valid = Form.validate(self)
        if(valid):
            if not is_valid_phone(self.phone.data):
                self.phone.errors.append('Invalid phone.')
                valid =  False
            if not is_valid_facebook_link(self.facebook_link.data):
                self.facebook_link.errors.append('Invalid facebook link.')
                valid = False
        return valid




class ArtistForm(Form):
    name = StringField(
        'name', validators=[DataRequired()]
    )
    city = StringField(
        'city', validators=[DataRequired()]
    )
    state = SelectField(
        'state', validators=[DataRequired()],
        choices = States.choices()
    )
    phone = StringField(
        # TODO implement validation logic for state
        'phone'
    )
    image_link = StringField(
        'image_link'
        
    )
    genres = SelectMultipleField(
        'genres', validators=[DataRequired()],
        choices=Genre.choices()
     )
    facebook_link = StringField(
        # TODO implement enum restriction
        'facebook_link'
     )

    website_link = StringField(
        'website_link'
     )

    seeking_venue = BooleanField( 'seeking_venue' )

    seeking_description = StringField(
            'seeking_description'
     )

    def validate(self):        
        def is_valid_phone(number):
            regex = re.compile('^\([0-9]{3}\) *[0-9]{3}-[0-9]{4}$|^[0-9]{3}-[0-9]{3}-[0-9]{4}$|^[0-9]{3}.[0-9]{3}.[0-9]{4}$|^$')
            return regex.match(number)

        def is_valid_facebook_link(facebookLink):
            # if valid or empty, count as valid
            if validators.url(facebookLink) or re.compile('^$').match(facebookLink):
                return True
            else: return False
        
        # perform default validation first
        valid = Form.validate(self)
        if (valid):
            if not is_valid_phone(self.phone.data):
                self.phone.errors.append('Invalid phone.')
                valid =  False
            if not is_valid_facebook_link(self.facebook_link.data):
                self.facebook_link.errors.append('Invalid facebook link.')
                valid = False
        return valid
