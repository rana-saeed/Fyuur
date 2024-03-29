#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_wtf import Form
from flask_migrate import Migrate
from sqlalchemy import func
from sqlalchemy_utils import PhoneNumberType
import logging
from logging import Formatter, FileHandler
from forms import *
from models import db
from models import Venue, Artist, Show
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')

db.init_app(app)
with app.app_context():
    db.create_all()

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  data = db.session.query(Venue.city, Venue.state
                          ,func.count('name')).group_by('city', 'state').all()
  class Area(object):
    def __init__(self, city, state, venues):
        self.city = city
        self.state = state
        self.venues = venues
  areas = []

  for area in data:
    venues = db.session.query(Venue.name, Venue.id).filter(Venue.city==area[0]).all()
    area = Area(area.city, area.state, venues)
    areas.append(area)
  return render_template('pages/venues.html', areas=areas);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  results = db.session.query(Venue.name, Venue.id).filter(Venue.name.ilike('%' + search_term + '%')).all()

  class SearchResults(object):
    def __init__(self, count, venues):
        self.count = count
        self.venues = venues
  searchResults = SearchResults(len(results), results)
  return render_template('pages/search_venues.html', results=searchResults, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

  #remove extra {} inserted in form
  data = db.session.query(Venue.genres).filter(Venue.id==venue_id).all()
  genres = data[0].genres.replace("{", "").replace("}", "")
  db.session.query(Venue).filter(Venue.id==venue_id).update({"genres": genres})
  db.session.commit()

  data = db.session.query(Venue.id,
                          Venue.name,
                          Venue.city,
                          Venue.state,
                          Venue.address,
                          Venue.phone,
                          Venue.genres,
                          Venue.image_link,
                          Venue.facebook_link,
                          Venue.website,
                          Venue.seeking_talent,
                          Venue.seeking_description).filter(Venue.id==venue_id).all()

  upcomingShows = db.session.query(Artist.id,
                                  Artist.name,
                                  Artist.image_link,
                                  Show.date).join(Show).filter(Artist.id == Show.artist_id, Show.venue_id==venue_id, Show.date>datetime.now()).all()

  pastShows = db.session.query(Artist.id,
                                Artist.name,
                                Artist.image_link,
                                Show.date).join(Show).filter(Artist.id == Show.artist_id, Show.venue_id==venue_id, Show.date<datetime.now()).all()
  
  upcomingShowsCount = len(upcomingShows)
  pastShowsCount = len(pastShows)
  return render_template('pages/show_venue.html', venue=data[0], upcomingShows=upcomingShows, upcomingShowsCount=upcomingShowsCount, pastShows=pastShows, pastShowsCount=pastShowsCount)

#  Create Venue
#  ----------------------------------------------------------------
@app.route('/venues/create', methods=['GET', 'POST'])
def create_venue():
    form = VenueForm(request.form)
    if request.method == 'POST' and form.validate():
      error = False
      body = {}

      try:
        genres = []   
        seeking_talent = False

        if('genres' in request.form):
          genres=request.form.getlist('genres')
        if('seeking_talent' in request.form):
          seeking_talent= True        

        venue = Venue(name= request.form['name'],
                      city= request.form['city'],
                      state= request.form['state'],
                      address= request.form['address'],
                      phone= request.form['phone'],
                      genres= genres,
                      image_link= request.form['image_link'],
                      website= request.form['website'],
                      facebook_link= request.form['facebook_link'],
                      seeking_talent= seeking_talent,
                      seeking_description= request.form['seeking_description'])

        db.session.add(venue)
        db.session.commit()
      except:
        error = True
        db.session.rollback()
        print(sys.exc_info)
      finally:
        db.session.close()
    
      if error:
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
      else:
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
      
      return render_template('pages/home.html')
    return render_template('forms/new_venue.html', form=form)

@app.route('/venues/<int:venue_id>/edit', methods=['GET', 'POST'])
def edit_venue(venue_id):
    form = VenueForm(request.form)
    
    if request.method == 'GET':
      venue = db.session.query(Venue.id,
                                Venue.name,
                                Venue.city,
                                Venue.state,
                                Venue.address,
                                Venue.phone,
                                Venue.genres,
                                Venue.image_link,
                                Venue.facebook_link,
                                Venue.website,
                                Venue.seeking_talent,
                                Venue.seeking_description).filter(Venue.id==venue_id).all()
      formEditable = VenueForm(obj=venue[0])
      return render_template('forms/edit_venue.html', form=formEditable, venue=venue[0])

    if request.method == 'POST' and form.validate():
      error = False
      try:
        db.session.query(Venue).filter(Venue.id==venue_id).update({"name": request.form['name']})
        db.session.query(Venue).filter(Venue.id==venue_id).update({"city": request.form['city']})
        db.session.query(Venue).filter(Venue.id==venue_id).update({"state": request.form['state']})
        db.session.query(Venue).filter(Venue.id==venue_id).update({"address": request.form['address']})
        db.session.query(Venue).filter(Venue.id==venue_id).update({"phone": request.form['phone']})
        db.session.query(Venue).filter(Venue.id==venue_id).update({"image_link": request.form['image_link']})
        db.session.query(Venue).filter(Venue.id==venue_id).update({"facebook_link": request.form['facebook_link']})
        db.session.query(Venue).filter(Venue.id==venue_id).update({"website": request.form['website']})
        db.session.query(Venue).filter(Venue.id==venue_id).update({"seeking_description": request.form['seeking_description']})

        if('genres' in request.form):
          db.session.query(Venue).filter(Venue.id==venue_id).update({"genres": request.form.getlist('genres')})

        if('seeking_talent' in request.form):
          db.session.query(Venue).filter(Venue.id==venue_id).update({"seeking_talent": request.form['seeking_talent']})
        else:
          db.session.query(Venue).filter(Venue.id==venue_id).update({"seeking_talent": False})
        
        db.session.commit()
      except:
        error = True
        db.session.rollback()
        print(sys.exc_info)
      finally:
        db.session.close()
      if error:
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be edited.')
      else:
        flash('Venue ' + request.form['name'] + ' was successfully edited!')
      return redirect(url_for('show_venue' , venue_id=venue_id))
    return redirect(url_for('show_venue' , venue_id=venue_id))


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  body={}
  deleted = True
  try:
    name = db.session.query(Venue.name, Venue.id).filter_by(id=venue_id).all()
    body['name'] = name[0]
    
    venue = db.session.query(Venue.id).filter_by(id=venue_id).delete()
    db.session.commit()
  except:
    deleted = False
    db.session.rollback()
  finally:
    db.session.close()
  
  if deleted:
    flash('Venue ' + body['name'] + ' was successfully deleted!')
  else:
    flash('Venue ' + body['name'] + ' could not be deleted!')
  return redirect(url_for('venues'))
  # TODO: BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = db.session.query( Artist.id, Artist.name).order_by(Artist.name).all()
  print(data[0].id)
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term', '')
  results = db.session.query(Artist.name, Artist.id).filter(Artist.name.ilike('%' + search_term + '%')).all()
  class SearchResults(object):
    def __init__(self, count, artists):
        self.count = count
        self.artists = artists
  searchResults = SearchResults(len(results), results)
  return render_template('pages/search_artists.html', results=searchResults, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  #remove extra {} inserted in form
  data = db.session.query(Artist.genres).filter(Artist.id==artist_id).all()
  genres = data[0].genres.replace("{", "").replace("}", "")
  db.session.query(Artist).filter(Artist.id==artist_id).update({"genres": genres})
  db.session.commit()

  data = db.session.query(Artist.id,
                          Artist.name,
                          Artist.city,
                          Artist.state,
                          Artist.phone,
                          Artist.genres,
                          Artist.image_link,
                          Artist.facebook_link,
                          Artist.website,
                          Artist.seeking_venue,
                          Artist.seeking_description).filter(Artist.id==artist_id).all()

  upcomingShows = db.session.query(Venue.id,
                                  Venue.name,
                                  Venue.image_link,
                                  Show.date).join(Show).filter(Venue.id == Show.venue_id, Show.artist_id==artist_id, Show.date>datetime.now()).all()
  pastShows = db.session.query(Venue.id,
                                Venue.name,
                                Venue.image_link,
                                Show.date).join(Show).filter(Venue.id == Show.venue_id, Show.artist_id==artist_id, Show.date<datetime.now()).all()
  
  upcomingShowsCount = len(upcomingShows)
  pastShowsCount = len(pastShows)

  return render_template('pages/show_artist.html', artist=data[0], upcomingShows=upcomingShows, upcomingShowsCount=upcomingShowsCount, pastShows=pastShows, pastShowsCount=pastShowsCount)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET', 'POST'])
def edit_artist(artist_id):
    form = ArtistForm(request.form)
    
    if request.method == 'GET':
      artist = db.session.query(Artist.id,
                                Artist.name,
                                Artist.city,
                                Artist.state,
                                Artist.phone,
                                Artist.genres,
                                Artist.image_link,
                                Artist.facebook_link,
                                Artist.website,
                                Artist.seeking_venue,
                                Artist.seeking_description).filter(Artist.id==artist_id).all()
      
      formEditable = ArtistForm(obj=artist[0])
      return render_template('forms/edit_artist.html', form=formEditable, artist=artist[0])

    if request.method == 'POST' and form.validate():
      error = False
      try:
        db.session.query(Artist).filter(Artist.id==artist_id).update({"name": request.form['name']})
        db.session.query(Artist).filter(Artist.id==artist_id).update({"city": request.form['city']})
        db.session.query(Artist).filter(Artist.id==artist_id).update({"state": request.form['state']})
        db.session.query(Artist).filter(Artist.id==artist_id).update({"phone": request.form['phone']})
        db.session.query(Artist).filter(Artist.id==artist_id).update({"image_link": request.form['image_link']})
        db.session.query(Artist).filter(Artist.id==artist_id).update({"facebook_link": request.form['facebook_link']})
        db.session.query(Artist).filter(Artist.id==artist_id).update({"website": request.form['website']})
        
        if('genres' in request.form):
          db.session.query(Artist).filter(Artist.id==artist_id).update({"genres": request.form.getlist('genres')})

        if('seeking_venue' in request.form):
          db.session.query(Artist).filter(Artist.id==artist_id).update({"seeking_venue": request.form['seeking_venue']})
        else:
          db.session.query(Artist).filter(Artist.id==artist_id).update({"seeking_venue": False})
        
        db.session.commit()
      except:
        error = True
        db.session.rollback()
        print(sys.exc_info)
      finally:
        db.session.close()
      if error:
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be edited.')
      else:
        flash('Artist ' + request.form['name'] + ' was successfully edited!')
      return redirect(url_for('show_artist' , artist_id=artist_id))
    return redirect(url_for('show_artist' , artist_id=artist_id))

#  Create Artist
#  ----------------------------------------------------------------
@app.route('/artists/create', methods=['GET', 'POST'])
def create_artist():
    form = ArtistForm(request.form)
    if request.method == 'POST' and form.validate():
      error = False
      body = {}

      try:      
        genres = []            
        seeking_venue = False
        
        if('genres' in request.form):
          genres = request.form.getlist('genres')
        if('seeking_venue' in request.form):
          seeking_venue= True

        artist = Artist(name= request.form['name'],
                        city= request.form['city'],
                        state= request.form['state'],
                        phone= request.form['phone'],
                        genres= genres,
                        image_link= request.form['image_link'],
                        website= request.form['website'],
                        facebook_link= request.form['facebook_link'],
                        seeking_venue= seeking_venue,
                        seeking_description= request.form['seeking_description'])

        db.session.add(artist)
        db.session.commit()
      except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
      finally:
        db.session.close()
      if error:
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
      else:
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
      
      return render_template('pages/home.html')
    return render_template('forms/new_artist.html', form=form)

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  artists = []
  venues = []

  data = db.session.query(Show.id,
                          Show.venue_id,
                          Show.artist_id,
                          Show.date).all()
  for show in data:
    artists.append(db.session.query(Artist.id, Artist.name, Artist.image_link).join(Show).filter(Artist.id == show.artist_id).first())
    venues.append(db.session.query(Venue.id, Venue.name).join(Show).filter(Venue.id == show.venue_id).first())
  return render_template('pages/shows.html', shows_artists_venues=zip(data,artists,venues))

@app.route('/shows/create', methods=['GET', 'POST'])
def create_show():
    form = ShowForm(request.form)
    if request.method == 'POST' and form.validate():
      error = False
      body = {}

      try:                  
        show = Show(date= request.form['date'],
                    venue_id= request.form['venue_id'],
                    artist_id= request.form['artist_id'])

        db.session.add(show)
        db.session.commit()
      except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
      finally:
        db.session.close()
      if error:
        flash('An error occurred. Show on ' + request.form['date'] + ' could not be listed.')
      else:
        flash('Show on ' + request.form['date'] + ' was successfully listed!')
      
      return render_template('pages/home.html')
    return render_template('forms/new_show.html', form=form)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500

if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.debug = True
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
