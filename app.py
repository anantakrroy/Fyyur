#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import config
import datetime
from datetime import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    genres = db.Column(db.ARRAY(db.String))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website = db.Column(db.String)
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    show_venue_id = db.relationship(
        'Show', backref='venueshows', passive_deletes=True)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String), nullable=False)
    website = db.Column(db.String)
    seeking_description = db.Column(db.String)
    seeking_venue = db.Column(db.String)
    image_link = db.Column(db.String(500), unique=True)
    facebook_link = db.Column(db.String(120))

    show_artist_id = db.relationship(
        'Show', backref='artistshows', passive_deletes=True)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.


class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey(
        "Venue.id", ondelete='CASCADE'))
    artist_id = db.Column(db.Integer, db.ForeignKey(
        "Artist.id", ondelete='CASCADE'))
    start_time = db.Column(db.DateTime)


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Helper Functions.
#----------------------------------------------------------------------------#


def shows_count(id):
    all_shows = db.session.query(Show).all()
    return len(all_shows)


def pastShowsVenue(id):
    past_shows = []
    today = datetime.today()
    all_shows = db.session.query(Show).all()
    for show in all_shows:
        show_time = show.start_time
        days_left = (show_time - today).days
        if days_left < 0:
            past_shows.append({
                'artist_id': show[0].artist_id,
                'artist_name': show[1],
                'artist_image_link': show[2],
                'start_time': format_datetime((db.session.query(Show).all()[id].start_time).strftime("%d/%m/%Y, %H:%M:%S"))
            })
    return past_shows


def pastShowsArtist(id):
    past_shows = []
    today = datetime.today()
    all_shows = db.session.query(Show, Venue.name, Venue.image_link).join(
        Show).filter_by(artist_id=id).all()
    for show in all_shows:
        show_time = show[0].start_time
        days_left = (show_time - today).days
        if days_left < 0:
            past_shows.append({
                'venue_id': show[0].venue_id,
                'venue_name': show[1],
                'venue_image_link': show[2],
                'start_time': format_datetime((db.session.query(Show).all()[id].start_time).strftime("%d/%m/%Y, %H:%M:%S"))
            })
    return past_shows


def upcomingShowsVenue(id):
    upcoming_shows = []
    today = datetime.today()
    all_shows = db.session.query(Show, Artist.name, Artist.image_link).join(
        Show).filter_by(venue_id=id).all()
    for show in all_shows:
        show_time = show[0].start_time
        days_left = (show_time - today).days
        if days_left > 0:
            upcoming_shows.append({
                'artist_id': show[0].artist_id,
                'artist_name': show[1],
                'artist_image_link': show[2],
                'start_time': format_datetime(show_time.strftime("%d/%m/%Y, %H:%M:%S"))
            })
    return upcoming_shows


def upcomingShowsArtist(id):
    upcoming_shows = []
    today = datetime.today()
    all_shows = db.session.query(Show, Venue.name, Venue.image_link).join(
        Show).filter_by(artist_id=id).all()
    for show in all_shows:
        show_time = show[0].start_time
        days_left = (show_time - today).days
        if days_left > 0:
            upcoming_shows.append({
                'venue_id': show[0].venue_id,
                'venue_name': show[1],
                'venue_image_link': show[2],
                'start_time': format_datetime(show_time.strftime("%d/%m/%Y, %H:%M:%S"))
            })
    return upcoming_shows
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
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    all_venues = db.session.query(Venue).all()
    unique_cities = db.session.query(Venue).distinct(Venue.city).all()

    data = []

    for city in unique_cities:
        venues_in_city = []
        for venue in all_venues:
            if(venue.city == city.city):
                venues_in_city.append({
                    'id': venue.id,
                    'name': venue.name,
                    'num_upcoming_shows': shows_count(venue.id)
                })
        data.append({
                    'city': city.city,
                    'state': city.state,
                    'venues': venues_in_city
                    })

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_term = request.form.get('search_term')
    data = []
    all_venues = db.session.query(Venue).all()
    for venue in all_venues:
        if(search_term.lower() in venue.name.lower()):
            data.append({
                'id': venue.id,
                'name': venue.name,
                'num_upcoming_shows': len(upcomingShowsVenue(venue.id))
            })

    response = {
        "count": len(data),
        "data": data
    }

    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    data = []
    all_queried_venues = db.session.query(Venue).filter_by(id=venue_id).all()
    for venue in all_queried_venues:
        data.append({
            'id': venue.id,
            'name': venue.name,
            'genres': venue.genres,
            'address': venue.address,
            'city': venue.city,
            'state': venue.state,
            'phone': venue.phone,
            'website': venue.website,
            'facebook_link': venue.facebook_link,
            'seeking_talent': venue.seeking_talent,
            'image_link': venue.image_link,
            'past_shows': pastShowsVenue(venue_id),
            'upcoming_shows': upcomingShowsVenue(venue_id),
            'past_shows_count': len(pastShowsVenue(venue_id)),
            'upcoming_shows_count': len(upcomingShowsVenue(venue_id))
        })
    return render_template('pages/show_venue.html', venue=data[0])

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    form = VenueForm()
    if form.validate_on_submit():
        form_data = form.data
        venue = Venue(name=form_data['name'], city=form_data['city'], state=form_data['state'], address=form_data['address'],
                      phone=form_data['phone'], image_link=form_data['image_link'], genres=form_data['genres'], facebook_link=form_data['facebook_link'])
        db.session.add(venue)
        db.session.commit()
        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
        return render_template('pages/home.html')

    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    error_types = form.errors.keys()
    for e_type in error_types:
        for error in form.errors[e_type]:
            flash(error)
    return redirect(url_for('create_venue_submission'))


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    venue_delete = db.session.query(Venue).filter_by(id=venue_id).delete()
    try:
        db.session.commit()
    except AssertionError as err:
        db.session.rollback()
        abort(409, err)
    except Exception as err:
        db.session.rollback()
        abort(500, err)
    finally:
        db.session.close()
    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    data = Artist.query.all()
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".

    data = []
    search_query = request.form.get('search_term')
    all_artists = Artist.query.all()
    for artist in all_artists:
        if(search_query.lower() in artist.name.lower()):
            data.append({'id': artist.id, 'name': artist.name})
    response = {'count': len(data), 'data': data}

    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    artist = Artist.query.filter_by(id=artist_id).all()[0]
    data = {
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
        'image_link': artist.image_link,
        'past_shows': pastShowsArtist(artist_id),
        'past_shows_count': len(pastShowsArtist(artist_id)),
        'upcoming_shows': upcomingShowsArtist(artist_id),
        'upcoming_shows_count': len(upcomingShowsArtist(artist_id))
    }
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = {
        "id": 4,
        "name": "Guns N Petals",
        "genres": ["Rock n Roll"],
        "city": "San Francisco",
        "state": "CA",
        "phone": "326-123-5000",
        "website": "https://www.gunsnpetalsband.com",
        "facebook_link": "https://www.facebook.com/GunsNPetals",
        "seeking_venue": True,
        "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
        "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
    }
    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.filter_by(id=venue_id).all()[0]
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    print('New form data >> ', request.form.get())
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    form = ArtistForm()
    if form.validate_on_submit():
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    # on successful db insert, flash success
    for error in form.errors['phone']:
        print(error)
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    data = [{
        "venue_id": 1,
        "venue_name": "The Musical Hop",
        "artist_id": 4,
        "artist_name": "Guns N Petals",
        "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
        "start_time": "2019-05-21T21:30:00.000Z"
    }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 5,
        "artist_name": "Matt Quevedo",
        "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
        "start_time": "2019-06-15T23:00:00.000Z"
    }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 6,
        "artist_name": "The Wild Sax Band",
        "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
        "start_time": "2035-04-01T20:00:00.000Z"
    }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 6,
        "artist_name": "The Wild Sax Band",
        "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
        "start_time": "2035-04-08T20:00:00.000Z"
    }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 6,
        "artist_name": "The Wild Sax Band",
        "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
        "start_time": "2035-04-15T20:00:00.000Z"
    }]
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead

    # on successful db insert, flash success
    flash('Show was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
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
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
