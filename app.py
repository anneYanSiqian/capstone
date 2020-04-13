import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from auth import AuthError, requires_auth
from models import db_drop_and_create_all, setup_db, Person, Game, Performance
from config import pagination
from flask_migrate import Migrate

ROWS_PER_PAGE = pagination['example']

def create_app(test_config=None):
  '''create and configure the app'''
  
  app = Flask(__name__)
  setup_db(app)
  # db_drop_and_create_all() # uncomment this if you want to start a new database on app refresh

  #----------------------------------------------------------------------------#
  # CORS (API configuration)
  #----------------------------------------------------------------------------#

  CORS(app)
  # CORS Headers 
  @app.after_request
  def after_request(response):
      response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
      response.headers.add('Access-Control-Allow-Methods', 'GET,PATCH,POST,DELETE,OPTIONS')
      return response

  #----------------------------------------------------------------------------#
  # Custom Functions
  #----------------------------------------------------------------------------#

  def get_error_message(error, default_text):
      '''Returns default error text or custom error message (if not applicable)

      *Input:
          * <error> system generated error message which contains a description message
          * <string> default text to be used as error message if Error has no specific message
      *Output:
          * <string> specific error message or default text(if no specific message is given)

      '''
      try:
          # Return message contained in error, if possible
          return error.description['message']
      except:
          # otherwise, return given default text
          return default_text

  def paginate_results(request, selection):
    '''Paginates and formats database queries

    Parameters:
      * <HTTP object> request, that may contain a "page" value
      * <database selection> selection of objects, queried from database
    
    Returns:
      * <list> list of dictionaries of objects, max. 10 objects

    '''
    # Get page from request. If not given, default to 1
    page = request.args.get('page', 1, type=int)
    
    # Calculate start and end slicing
    start =  (page - 1) * ROWS_PER_PAGE
    end = start + ROWS_PER_PAGE

    # Format selection into list of dicts and return sliced
    objects_formatted = [object_name.format() for object_name in selection]
    return objects_formatted[start:end]

  #----------------------------------------------------------------------------#
  #  API Endpoints
  #  ----------------------------------------------------------------
  #  NOTE:  For explanation of each endpoint, please have look at the README.md file. 
  #         DOC Strings only contain short description and list of test classes 
  #----------------------------------------------------------------------------#

  #----------------------------------------------------------------------------#
  # Endpoint /persons GET/POST/DELETE/PATCH
  #----------------------------------------------------------------------------#
  @app.route('/persons', methods=['GET'])
  @requires_auth('read:persons')
  def get_persons():
    """Returns paginated persons object

    Tested by:
      Success:
        - test_get_all_persons
      Error:
        - test_error_401_get_all_persons
        - test_error_404_get_persons

    """
    selection = Person.query.all()
    persons_paginated = paginate_results(request, selection)

    if len(persons_paginated) == 0:
      abort(404, {'message': 'no persons found in database.'})

    return jsonify({
      'success': True,
      'persons': persons_paginated
    })

  @app.route('/persons', methods=['POST'])
  @requires_auth('create:persons')
  def insert_persons():
    """Inserts a new Person

    Tested by:
      Success:
        - test_create_new_person
      Error:
        - test_error_422_new_person
        - test_error_401_new_person

    """
    # Get request json
    body = request.get_json()

    if not body:
          abort(400, {'message': 'request does not contain a valid JSON body.'})

    # Extract name and age value from request body
    name = body.get('name', None)
    age = body.get('age', None)

    # Set gender to value or to 'Other' if not given
    gender = body.get('gender', 'Other')

    # abort if one of these are missing with appropiate error message
    if not name:
      abort(422, {'message': 'no name provided.'})

    if not age:
      abort(422, {'message': 'no age provided.'})

    # Create new instance of Person & insert it.
    new_person = (Person(
          name = name, 
          age = age,
          gender = gender
          ))
    new_person.insert()

    return jsonify({
      'success': True,
      'created': new_person.id
    })

  @app.route('/persons/<person_id>', methods=['PATCH'])
  @requires_auth('edit:persons')
  def edit_persons(payload, person_id):
    """Edit an existing Person

    Tested by:
      Success:
        - test_edit_person
      Error:
        - test_error_404_edit_person

    """
    # Get request json
    body = request.get_json()

    # Abort if no person_id or body has been provided
    if not person_id:
      abort(400, {'message': 'please append an person id to the request url.'})

    if not body:
      abort(400, {'message': 'request does not contain a valid JSON body.'})

    # Find person which should be updated by id
    person_to_update = Person.query.filter(Person.id == person_id).one_or_none()

    # Abort 404 if no person with this id exists
    if not person_to_update:
      abort(404, {'message': 'Person with id {} not found in database.'.format(person_id)})

    # Extract name and age value from request body
    # If not given, set existing field values, so no update will happen
    name = body.get('name', person_to_update.name)
    age = body.get('age', person_to_update.age)
    gender = body.get('gender', person_to_update.gender)

    # Set new field values
    person_to_update.name = name
    person_to_update.age = age
    person_to_update.gender = gender

    # Delete person with new values
    person_to_update.update()

    # Return success, updated person id and updated person as formatted list
    return jsonify({
      'success': True,
      'updated': person_to_update.id,
      'person' : [person_to_update.format()]
    })

  @app.route('/persons/<person_id>', methods=['DELETE'])
  @requires_auth('delete:persons')
  def delete_persons(payload, person_id):
    """Delete an existing Person

    Tested by:
      Success:
        - test_delete_person
      Error:
        - test_error_401_delete_person
        - test_error_404_delete_person

    """
    # Abort if no person_id has been provided
    if not person_id:
      abort(400, {'message': 'please append an person id to the request url.'})
  
    # Find person which should be deleted by id
    person_to_delete = Person.query.filter(Person.id == person_id).one_or_none()

    # If no person with given id could found, abort 404
    if not person_to_delete:
        abort(404, {'message': 'Person with id {} not found in database.'.format(person_id)})
    
    # Delete person from database
    person_to_delete.delete()
    
    # Return success and id from deleted person
    return jsonify({
      'success': True,
      'deleted': person_id
    })

  #----------------------------------------------------------------------------#
  # Endpoint /games GET/POST/DELETE/PATCH
  #----------------------------------------------------------------------------#
  @app.route('/games', methods=['GET'])
  @requires_auth('read:games')
  def get_games(payload):
    """Returns paginated games object

    Tested by:
      Success:
        - test_get_all_games
      Error:
        - test_error_401_get_all_games
        - test_error_404_get_games

    """
    selection = Game.query.all()
    games_paginated = paginate_results(request, selection)

    if len(games_paginated) == 0:
      abort(404, {'message': 'no games found in database.'})

    return jsonify({
      'success': True,
      'games': games_paginated
    })

  @app.route('/games', methods=['POST'])
  @requires_auth('create:games')
  def insert_games(payload):
    """Inserts a new game

    Tested by:
      Success:
        - test_create_new_game
      Error:
        - test_error_422_new_game
        - test_error_401_new_game

    """
    # Get request json
    body = request.get_json()

    if not body:
          abort(400, {'message': 'request does not contain a valid JSON body.'})

    # Extract title and release_date value from request body
    title = body.get('title', None)
    release_date = body.get('release_date', None)

    # abort if one of these are missing with appropiate error message
    if not title:
      abort(422, {'message': 'no title provided.'})

    if not release_date:
      abort(422, {'message': 'no "release_date" provided.'})

    # Create new instance of game & insert it.
    new_game = (Game(
          title = title, 
          release_date = release_date
          ))
    new_game.insert()

    return jsonify({
      'success': True,
      'created': new_game.id
    })

  @app.route('/games/<game_id>', methods=['PATCH'])
  @requires_auth('edit:games')
  def edit_games(payload, game_id):
    """Edit an existing Game

    Tested by:
      Success:
        - test_edit_game
      Error:
        - test_error_404_edit_game

    """
    # Get request json
    body = request.get_json()

    # Abort if no game_id or body has been provided
    if not game_id:
      abort(400, {'message': 'please append an game id to the request url.'})

    if not body:
      abort(400, {'message': 'request does not contain a valid JSON body.'})

    # Find game which should be updated by id
    game_to_update = Game.query.filter(Game.id == game_id).one_or_none()

    # Abort 404 if no game with this id exists
    if not game_to_update:
      abort(404, {'message': 'Game with id {} not found in database.'.format(game_id)})

    # Extract title and age value from request body
    # If not given, set existing field values, so no update will happen
    title = body.get('title', game_to_update.title)
    release_date = body.get('release_date', game_to_update.release_date)

    # Set new field values
    game_to_update.title = title
    game_to_update.release_date = release_date

    # Delete game with new values
    game_to_update.update()

    # Return success, updated game id and updated game as formatted list
    return jsonify({
      'success': True,
      'edited': game_to_update.id,
      'game' : [game_to_update.format()]
    })

  @app.route('/games/<game_id>', methods=['DELETE'])
  @requires_auth('delete:games')
  def delete_games(payload, game_id):
    """Delete an existing Game

    Tested by:
      Success:
        - test_delete_game
      Error:
        - test_error_401_delete_game
        - test_error_404_delete_game

    """
    # Abort if no game_id has been provided
    if not game_id:
      abort(400, {'message': 'please append an game id to the request url.'})
  
    # Find game which should be deleted by id
    game_to_delete = Game.query.filter(Game.id == game_id).one_or_none()

    # If no game with given id could found, abort 404
    if not game_to_delete:
        abort(404, {'message': 'Game with id {} not found in database.'.format(game_id)})
    
    # Delete game from database
    game_to_delete.delete()
    
    # Return success and id from deleted game
    return jsonify({
      'success': True,
      'deleted': game_id
    })

  #----------------------------------------------------------------------------#
  # Error Handlers
  #----------------------------------------------------------------------------#

  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
        "success": False, 
        "error": 422,
        "message": get_error_message(error,"unprocessable")
    }), 422

  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
        "success": False, 
        "error": 400,
        "message": get_error_message(error, "bad request")
    }), 400

  @app.errorhandler(404)
  def ressource_not_found(error):
    return jsonify({
        "success": False, 
        "error": 404,
        "message": get_error_message(error, "resource not found")
    }), 404

  @app.errorhandler(AuthError)
  def authentification_failed(AuthError): 
    return jsonify({
        "success": False, 
        "error": AuthError.status_code,
        "message": AuthError.error['description']
    }), AuthError.status_code


  # After every endpoint has been created, return app
  return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)