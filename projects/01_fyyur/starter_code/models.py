from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import PhoneNumberType


db = SQLAlchemy()

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(PhoneNumberType())
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500), nullable=False)
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean(), default=False)
    past_shows_count = db.Column(db.Integer)
    upcoming_shows_count = db.Column(db.Integer)
    past_shows = db.Column(db.PickleType)
    upcoming_shows = db.Column(db.PickleType)
    shows = db.relationship('Show', backref='venue', lazy='joined', innerjoin=True)

    def __repr__(self):
        return '<Venue {self.id} {self.name} {self.city} {self.state} {self.address} {self.phone} {self.genres}>'

class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(PhoneNumberType())
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean(), default=False)
    seeking_description = db.Column(db.String())
    past_shows_count = db.Column(db.Integer)
    upcoming_shows_count = db.Column(db.Integer)
    past_shows = db.Column(db.PickleType)
    upcoming_shows = db.Column(db.PickleType)
    shows = db.relationship('Show', backref='artist', lazy='joined', innerjoin=True)

class Show(db.Model):
    __tablename__ = 'show'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime(), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'),nullable=False )
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'),nullable=False )
    artist_name = db.Column(db.String())
    venue_name = db.Column(db.String())
    artist_image_link = db.Column(db.String(500))
    venue_image_link = db.Column(db.String(500))
