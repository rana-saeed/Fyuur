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
        seeking_talent = False
        if('seeking_talent' in request.form):
          seeking_talent= True
        
        venue = Venue(name= request.form['name'],
                      city= request.form['city'],
                      state= request.form['state'],
                      address= request.form['address'],
                      phone= request.form['phone'],
                      genres= request.form.getlist('genres'),
                      image_link= request.form['image_link'],
                      website= request.form['website'],
                      facebook_link= request.form['facebook_link'],
                      seeking_talent= seeking_talent,
                      past_shows= [],
                      past_shows_count= 0,
                      upcoming_shows= [],
                      upcoming_shows_count= 0)

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
                                Venue.seeking_talent).filter(Venue.id==venue_id).all()
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
        db.session.query(Venue).filter(Venue.id==venue_id).update({"genres": request.form.getlist('genres')})
        db.session.query(Venue).filter(Venue.id==venue_id).update({"image_link": request.form['image_link']})
        db.session.query(Venue).filter(Venue.id==venue_id).update({"facebook_link": request.form['facebook_link']})
        db.session.query(Venue).filter(Venue.id==venue_id).update({"website": request.form['website']})
        
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
    # return redirect(url_for('show_venue', venue_id=venue_id))
    return None


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
  
  return flask.redirect(flask.url_for('venues'))
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
                          Artist.seeking_description,
                          Artist.upcoming_shows_count,
                          Artist.upcoming_shows,
                          Artist.past_shows_count,
                          Artist.past_shows).filter(Artist.id==artist_id).all()

  upcomingShows = db.session.query(Venue.id,
                                Venue.name,
                                Venue.image_link,
                                Show.date).join(Show).filter(Venue.id == Show.venue_id, Show.artist_id==artist_id, Show.date>datetime.now()).all()

  upcomingShowsCount = db.session.query(Venue.id,
                                Venue.name,
                                Venue.image_link,
                                Show.date).join(Show).filter(Venue.id == Show.venue_id, Show.artist_id==artist_id, Show.date>datetime.now()).count()
  
  pastShows = db.session.query(Venue.id,
                                Venue.name,
                                Venue.image_link,
                                Show.date).join(Show).filter(Venue.id == Show.venue_id, Show.artist_id==artist_id, Show.date<datetime.now()).all()
  
  pastShowsCount = db.session.query(Venue.id,
                                Venue.name,
                                Venue.image_link,
                                Show.date).join(Show).filter(Venue.id == Show.venue_id, Show.artist_id==artist_id, Show.date<datetime.now()).count()
  for show in pastShows:
    db.session.query(Show).filter(Show.venue_id==show.id).update({"venue_name": show.name})
    db.session.query(Show).filter(Show.venue_id==show.id).update({"venue_image_link": show.image_link})

  for show in upcomingShows:
    db.session.query(Show).filter(Show.venue_id==show.id).update({"venue_name": show.name})
    db.session.query(Show).filter(Show.venue_id==show.id).update({"venue_image_link": show.image_link})

  db.session.query(Show).filter(Show.artist_id==artist_id).update({"artist_name": data[0].name})
  db.session.query(Show).filter(Show.artist_id==artist_id).update({"artist_image_link": data[0].image_link})

  db.session.query(Artist).filter(Artist.id==artist_id).update({"upcoming_shows_count": upcomingShowsCount})
  db.session.query(Artist).filter(Artist.id==artist_id).update({"past_shows_count": pastShowsCount})
  db.session.query(Artist).filter(Artist.id==artist_id).update({"upcoming_shows": upcomingShows})                                                          
  db.session.query(Artist).filter(Artist.id==artist_id).update({"past_shows": pastShows})
  db.session.commit()
                   
  return render_template('pages/show_artist.html', artist=data[0])

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
        db.session.query(Artist).filter(Artist.id==artist_id).update({"genres": request.form.getlist('genres')})
        db.session.query(Artist).filter(Artist.id==artist_id).update({"image_link": request.form['image_link']})
        db.session.query(Artist).filter(Artist.id==artist_id).update({"facebook_link": request.form['facebook_link']})
        db.session.query(Artist).filter(Artist.id==artist_id).update({"website": request.form['website']})
        
        if('seeking_venue' in request.form):
          db.session.query(Artist).filter(Artist.id==artist_id).update({"seeking_venue": request.form['seeking_venue']})
          if('seeking_description' in request.form):
            db.session.query(Artist).filter(Artist.id==artist_id).update({"seeking_description": request.form['seeking_description']})
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
    return redirect(url_for('show_artist', artist_id=artist_id))

#  Create Artist
#  ----------------------------------------------------------------
@app.route('/artists/create', methods=['GET', 'POST'])
def create_artist():
    form = ArtistForm(request.form)
    if request.method == 'POST' and form.validate():
      print("HEREEEEEEE")
      error = False
      body = {}

      try:                  
        seeking_venue = False
        seeking_description = ""
        if('seeking_venue' in request.form):
          seeking_venue= True
          if('seeking_description' in request.form):
            seeking_description = request.form['seeking_description']
        
        artist = Artist(name= request.form['name'],
                      city= request.form['city'],
                      state= request.form['state'],
                      phone= request.form['phone'],
                      genres= request.form.getlist('genres'),
                      image_link= request.form['image_link'],
                      website= request.form['website'],
                      facebook_link= request.form['facebook_link'],
                      seeking_venue= seeking_venue,
                      seeking_description= seeking_description,
                      past_shows= [],
                      past_shows_count= 0,
                      upcoming_shows= [],
                      upcoming_shows_count= 0)

        db.session.add(artist)
        db.session.commit()
      except:
        error = True
        db.session.rollback()
        print(sys.exc_info)
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
  data = db.session.query(Show.id,
                   Show.venue_id,
                   Show.artist_id,
                   Show.date,
                   Show.venue_name,
                   Show.artist_name,
                   Show.venue_image_link,
                   Show.artist_image_link).all()
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create', methods=['GET', 'POST'])
def create_show():
    form = ShowForm(request.form)
    if request.method == 'POST' and form.validate():
      error = False
      body = {}

      try:                  
        show = Show(date= request.form['date'],
                    venue_id= request.form['venue_id'],
                    artist_id= request.form['artist_id'],
                    venue_name= "",
                    artist_name= "",
                    venue_image_link= "",
                    artist_image_link= "")

        artist = db.session.query(Artist.id,
                                  Artist.name,
                                  Artist.image_link).join(Show).filter(Artist.id == show.artist_id).all() 
        
        venue = db.session.query(Venue.id,
                                Venue.name,
                                Venue.image_link).join(Show).filter(Venue.id == show.venue_id).all() 
       
        show.artist_name = artist[0].name
        show.artist_image_link = artist[0].image_link
        show.venue_name = venue[0].name
        show.venue_image_link = venue[0].image_link

        db.session.add(show)
        db.session.commit()
      except:
        error = True
        db.session.rollback()
        print(sys.exc_info)
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
