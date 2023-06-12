#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import babel
from flask import render_template, request, Response, flash, redirect, url_for, abort
import dateutil.parser
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import collections
import collections.abc
import sys
from sqlalchemy.orm import sessionmaker
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from werkzeug.datastructures import MultiDict
import traceback
from models import Venue, Artist, Show
from start import app, db
# App Config.
collections.Callable = collections.abc.Callable

# Error handling
app.logger.setLevel(logging.ERROR)
errorHandler = RotatingFileHandler('error.log', maxBytes=10000, backupCount=1)
app.logger.setLevel(logging.ERROR)
app.logger.addHandler(errorHandler)

class NoSuchId(Exception):
  pass
class InvalidData(Exception):
  pass

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

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
  # get info for all venues grouped by cities
  def getCities(venues):
    # make an empty array for cities with their venues
    cityProfiles = []
    # get a list of city and state tuples in which each city and state tuple is unique
    cities = set((venue.city, venue.state) for venue in venues)
    # attach a group of venues with their info to each city in the list
    for city in cities:
      # make an empty dictionary for the city that will include all the venues
      info = {}
      
      # add name of the city
      info['city'] = city[0]
      
      # add name of the state
      info['state'] = city[1]
      
      # add all the venues with their info
      # first get all the venues with the given city 
      listOfVenues = list(filter(
        lambda venue: (venue.city == info['city']),  
        venues))
      # make a list of info for every venue in the list of venues
      info['venues'] = [({
        'id': venue.id, 
        'name': venue.name, 
        'num_upcoming_shows': getNumberOfUpcomingShows(venue)
        }) for venue in listOfVenues]
      # add the whole info for the group of venues to the list of cities with their info
      cityProfiles.append(info)
    return cityProfiles

  def getNumberOfUpcomingShows(venue):
    now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    return db.session.query(Show).join(Venue.shows).filter(Venue.id == venue.id).filter(Show.start_time >= now).count()

  # get and render info for all venues  
  data = []
  try:
    # get info grouped by venues
    data = getCities(Venue.query.all())
  except Exception:
    print(sys.exc_info())
    traceback.print_exc()
    app.logger.error('Error retrieving list of venues from the database')
  finally: db.session.close()
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  def getNumberOfUpcomingShows(venue):
    now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    return db.session.query(Show).join(Venue.shows).filter(Venue.id == venue.id).filter(Show.start_time >= now).count()
  
  # get venues
  try:
    # get string to search for
    word = request.form.get('search_term')
    # make the searth in the database
    results = Venue.query.filter(Venue.name.ilike(f'%{word}%')).all()
    # get needed info from the search results
    response = {
      'count': len(results),
      'data': [
        {
        'id': result.id,
        'name': result.name,
        'num_upcoming_shows': getNumberOfUpcomingShows(result)
        } for result in results
      ]
    }
  except:
    print(sys.exc_info()) 
    app.logger.error('Error finding venues')
  finally: db.session.close()
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  def getInfo(venue):
    shows = getShows(venue)
    return {
      'id': venue.id,
      'name': venue.name,
      'genres': [] if (venue.genres is None) else venue.genres,
      'address': venue.address,
      'city': venue.city,
      'state': venue.state,
      'phone': venue.phone,
      'website': venue.website,
      'facebook_link': venue.facebook_link,
      'seeking_talent': venue.seeking_talent,
      'seeking_description': venue.seeking_description,
      'image_link': venue.image_link,
      'upcoming_shows': [] if (venue.shows is None or shows['upcoming'] == 0) else shows['upcoming'],
      'past_shows': [] if (venue.shows is None or shows['past'] == 0) else shows['past'],
      'upcoming_shows_count': len(shows['upcoming']),
      'past_shows_count': len(shows['past'])
      }
  
  def getShows(venue):
    return {
      'upcoming': getUpcomingShows(venue),
      'past': getPastShows(venue),
    }

  def getUpcomingShows(venue):
    now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    results = db.session.query(Show).join(Venue.shows).filter(Venue.id == venue.id).filter(Show.start_time >= now).all()
    print('number of results:', len(results))
    print('results:')
    print([result for result in results])
    return [{
      'artist_id': show.artist.id,
      'artist_name': show.artist.name,
      'artist_image_link': show.artist.image_link,
      'start_time': show.start_time
    } for show in results]

  def getPastShows(venue):
    now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    results = db.session.query(Show).join(Venue.shows).filter(Venue.id == venue.id).filter(Show.start_time < now).all()
    return [{
      'artist_id': show.artist.id,
      'artist_name': show.artist.name,
      'artist_image_link': show.artist.image_link,
      'start_time': show.start_time
    } for show in results]

  # get info
  # first make a list to return even if there is an exception
  data = []
  try:
    # find the venue (it will actually be just one)
    result = Venue.query.filter_by(id=venue_id).all()
    # report error if thera is no venue with the given id
    if (len(result) == 0):
      raise NoSuchId
    # get info if there is a venues with the given id
    data = getInfo(result[0])
  except NoSuchId:
    app.logger.error('No such venue id')
    abort(404)
  except Exception:
    app.logger.error('Error retrieving info about the venue from the database')
    print(sys.exc_info())
    traceback.print_exc()
  finally: db.session.close()
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

  try:
    error = False
    form = VenueForm(request.form)
    if not form.validate():
      # create empty list for errors
      list = []
      # loop through errors in the form
      for field, error in form.errors.items():
       # add error to the list
       list.extend(error)
      # create empty message for errors
      message = ''
      # loop through errors in the list
      for error in list:
        # add error to the message
        message += ' ' + error
      raise InvalidData
    
    newVenue = Venue(
        name = form.name.data,
        city = form.city.data,
        state = form.state.data,
        address = form.address.data,
        phone = form.phone.data,
        image_link = form.image_link.data,
        facebook_link = form.facebook_link.data,
        genres = form.genres.data,
        website = form.website_link.data,
        seeking_talent = form.seeking_talent.data,
        seeking_description = form.seeking_description.data
      )
    db.session.add(newVenue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except InvalidData as e:
    error = True
    flash(message)
    app.logger.error('Invalid venue data')
  except:
    error = True
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')#data.name
    app.logger.error('Venue could not be listed')
    print(sys.exc_info())
  finally:
    db.session.close()
  return render_template('pages/home.html') if not error else render_template('forms/new_venue.html', form = form)

@app.route('/venues/<int:venue_id>/delete') #methods=['DELETE'])
def delete_venue(venue_id):
  
  try:
    if Venue.query.filter_by(id=venue_id).first() is None:
      raise NoSuchId
    venue = Venue.query.filter_by(id=venue_id).first()
    db.session.delete(venue)
    db.session.commit()
  except(NoSuchId):
    app.logger.error('No such venue id')
    abort(404)
  except:
    db.session.rollback()
    app.logger.error('Error deleting venue')
    print(sys.exc_info())
  finally:
    db.session.close()
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  try:
    data = [{'id': artist.id, 'name': artist.name} for artist in Artist.query.all()]
  except: app.logger.error('Error retrieving artists from the database')
  finally: db.session.close()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  def getNumberOfUpcomingShows(artist):
    now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    return db.session.query(Show).join(Artist.shows).filter(Artist.id == artist.id).filter(Show.start_time >= now).count()

  # get info 
  try:
    # get the string to look for
    word = request.form.get('search_term')
    # find artists
    results = Artist.query.filter(Artist.name.ilike(f'%{word}%')).all()
    # get the needed data from the results
    response = {
      'count': len(results),
      'data': [
        {
        'id': result.id,
        'name': result.name, 
        'num_upcoming_shows': getNumberOfUpcomingShows(result)
        } for result in results
      ]
    }
  except: 
    app.logger.error('Error finding artist')
    print(sys.exc_info())
  finally: db.session.close()
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):  
  def getUpcomingShows(artist):
    now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    results = db.session.query(Show).join(Artist.shows).filter(Artist.id == artist.id).filter(Show.start_time >= now).all()
    return [{
      'venue_id': show.venue.id,
      'venue_name': show.venue.name,
      'venue_image_link': show.venue.image_link,
      'start_time': show.start_time
    } for show in results]

  def getPastShows(artist):
    now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    results = db.session.query(Show).join(Artist.shows).filter(Artist.id == artist.id).filter(Show.start_time < now).all()
    return [{
      'venue_id': show.venue.id,
      'venue_name': show.venue.name,
      'venue_image_link': show.venue.image_link,
      'start_time': show.start_time
    } for show in results]

  # get info
  # first make an list fo return even if there is an exception
  data = []
  try:
    # get the artist with the given id (there will actually be just one)
    artists = Artist.query.filter_by(id=artist_id).all()
    # if there is no artist with the given id, raise error
    if len(artists) == 0:
      raise NoSuchId
    # if there is an artist with the given id, get a variable for this artist
    artist = artists[0]
    # get past and upcoming shows
    pastShows = getPastShows(artist)
    upcomingShows = getUpcomingShows(artist)
    # put into to "data" from "artist"
    data = {
      'id': artist.id,
      'name': artist.name,
      'city': artist.city,
      'state': artist.state,
      'phone': artist.phone,
      'genres': artist.genres,
      'image_link': artist.image_link,
      'facebook_link': artist.facebook_link,
      'website': artist.website,
      'seeking_venue': artist.seeking_venue,
      'seeking_description': artist.seeking_description,
      'past_shows': pastShows,
      'upcoming_shows': upcomingShows,
      'past_shows_count': len(pastShows),
      'upcoming_shows_count': len(upcomingShows)
    }
  except NoSuchId:
    app.logger.error('No such artist id')
    abort(404)
  except:
    db.session.rollback()
    app.logger.error('Error retrieving artist from the database')
    print(sys.exc_info())
  finally: db.session.close()
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  try:
    artist = Artist.query.filter_by(id=artist_id).first()
    if artist is None: raise NoSuchId
    # put data from artist gotten from the database into a dictionary
    artistDictionary = {
      'id': artist.id,
      'name': artist.name,
      'genres': artist.genres,
      'city': artist.city,
      'state': artist.state,
      'phone': artist.phone,
      'website': artist.website,
      'facebook_link': artist.facebook_link,
      'seeking_venue': artist.seeking_venue,
      'seeking_description': artist.seeking_description,
      'image_link': artist.image_link
    }
    # for data from the dictionary to form that will be rendered to the user
    form = ArtistForm(MultiDict(artistDictionary))
  except NoSuchId:
    app.logger.error('No such id for artist')
    abort(404)
  except:
    app.logger.error('Error retrieving artist info from the database')
    print(sys.exc_info())
  finally: db.session.close()
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  try:
    error = False
    # for data from the user into ArtistForm
    form = ArtistForm(request.form)
    # get a handle for the artist in the database for an update
    artist = db.session.query(Artist).filter_by(id=artist_id).first()
    # update the artist with (possibly invalid) data from the form but don't commit yet
    artist.name = form.name.data
    artist.city = form.city.data 
    artist.state = form.state.data
    artist.phone = form.phone.data 
    artist.genres= form.genres.data
    artist.image_link = form.image_link.data
    artist.facebook_link = form.facebook_link.data
    artist.website = form.website_link.data
    artist.seeking_venue = form.seeking_venue.data
    artist.seeking_description = form.seeking_description.data 
    
    # validate the form given by the user
    if not form.validate():
      # create empty list for errors
      list = []
      # loop through errors in the form
      for field, error in form.errors.items():
       # add error to the list
       list.extend(error)
      # create empty message for errors
      message = ''
      # loop through errors in the list
      for error in list:
        # add error to the message
        message += ' ' + error
      raise InvalidData
    
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully updated!')
  except InvalidData as e:
    error = True
    flash(message)
    app.logger.error('Invalid artist data')
  except Exception as e:
    error = True
    db.session.rollback()
    app.logger.error('Artist could not be updated in the database')
    flash('An error occurred. Artist ' + artist.name + ' could not be updated.')
    print(sys.exc_info())
  finally: db.session.close()
  # render the artist info page, but if error, stay of the artist form page with possibly invalid data just given by the user
  return redirect(url_for('show_artist', artist_id=artist_id)) if not error else render_template('forms/edit_artist.html', form=form, artist = artist)

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  try:
    error = False
    venue = Venue.query.filter_by(id=venue_id).first()
    if venue is None: raise NoSuchId
    # put data from the venue gotten from the database into a dictionary
    venueDictionary = {
      'id': venue.id,
      'name': venue.name,
      'city': venue.city,
      'state': venue.state,
      'address': venue.address,
      'phone': venue.phone,
      'image_link': venue.image_link,
      'facebook_link': venue.facebook_link,
      'genres': venue.genres,
      'website': venue.website,
      'seeking_talent': venue.seeking_talent,
      'seeking_description': venue.seeking_description
    }
    # put data from the dictionary to a VenueForm
    form = VenueForm(MultiDict(venueDictionary))
  except NoSuchId:
    error = True
    app.logger.error('No such id for venue')
    abort(404)
  except Exception:
    error = True
    app.logger.error('Error retrieving venue info from the database')
    print(sys.exc_info())
  finally: db.session.close()
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  try:
    error = False
    # create a VenueForm and populate with data given by the user
    form = VenueForm(request.form)
    # find the venue to update
    venue = db.session.query(Venue).filter_by(id=venue_id).first()
    # update the venue with (possibly invalid) data from the form, but don't commit yet
    venue.name = form.name.data
    venue.city = form.city.data 
    venue.state = form.state.data
    venue.address = form.address.data
    venue.phone = form.phone.data
    venue.image_link = form.image_link.data
    venue.facebook_link = form.facebook_link.data
    venue.genres= form.genres.data
    venue.website = form.website_link.data
    venue.seeking_talent = form.seeking_talent.data
    venue.seeking_description = form.seeking_description.data
    
    # validate form
    if not form.validate():
      # create empty list for errors
      list = []
      # loop through errors in the form
      for field, error in form.errors.items():
        # add error to the list
        list.extend(error)
      # create empty message for errors
      message = ''
      # loop through errors in the list
      for error in list:
        # add error to the message
        message += ' ' + error
      raise InvalidData
    
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  except InvalidData as e:
    error = True
    flash(message)
    app.logger.error('Invalid venue data')
  except Exception as e:
    error = True
    db.session.rollback()
    app.logger.error('Venue could not be updated in the database')
    flash('An error occurred. Venue ' + venue.name + ' could not be updated.')
    print(sys.exc_info())
  finally: db.session.close()
  # render venue info page, but, if error, stay on the venue form page and render invalid data to user for correction
  return redirect(url_for('show_venue', venue_id=venue_id)) if not error else render_template('forms/edit_venue.html', form=form, venue = venue)

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error = False
  try:
    form = ArtistForm(request.form)
    if not form.validate():
      # create empty list for errors
      list = []
      # loop through errors in the form
      for field, error in form.errors.items():
        # add error to the list
        list.extend(error)
      # create empty message for errors
      message = ''
      # loop through errors in the list
      for error in list:
        # add error to the message
        message += ' ' + error
      raise InvalidData
    # transfer data from form to artist model
    artist = Artist(
      name = form.name.data, 
      city = form.city.data, 
      state = form.state.data,
      phone = form.phone.data, 
      genres= form.genres.data,
      image_link = form.image_link.data,
      facebook_link = form.facebook_link.data,
      website = form.website_link.data,
      seeking_venue = form.seeking_venue.data,
      seeking_description = form.seeking_description.data
      )
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except InvalidData as e:
    error = True
    flash(message)
    app.logger.error('Invalid artist data')
  except:
    error = True
    db.session.rollback()
    app.logger.error('Artist could not be inserted into the database')
    flash('An error occurred. Artist ' + artist.name + ' could not be listed.')
    print(sys.exc_info())
  finally: db.session.close()
  return render_template('pages/home.html') if not error else render_template('forms/new_artist.html', form = form)


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows = db.session.query(Show).all()
  data = [{
    'venue_id': show.venue.id,
    'venue_name': show.venue.name,
    'artist_id': show.artist.id,
    'artist_name': show.artist.name,
    'artist_image_link': show.artist.image_link,
    'start_time': show.start_time
  } for show in shows]
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form = ShowForm(request.form)
  try:
    error = False
    show = Show(
      venue_id = form.venue_id.data,
      artist_id = form.artist_id.data,
      start_time = form.start_time.data 
    )
    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')
  except: 
    error = True
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
    app.logger.error('Error inserting the show into the database')
    print(sys.exc_info())
  finally:
    db.session.close()
  # if error, stay on the page
  return render_template('pages/home.html') if error == False else render_template('forms/new_show.html', form = form)

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
'''if __name__ == '__main__':
    app.run()'''

# Or specify port manually:

if __name__ == '__main__':
    #port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=3000)
