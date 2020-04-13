import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy
from app import create_app
from models import setup_db, db_drop_and_create_all, Person, Game, Performance, db_drop_and_create_all
from config import bearer_tokens
from sqlalchemy import desc
from datetime import date

# Create dict with Authorization key and Bearer token as values. 
# Later used by test classes as Header

casting_assistant_auth_header = {
    'Authorization': bearer_tokens['casting_assistant']
}

casting_director_auth_header = {
    'Authorization': bearer_tokens['casting_director']
}

executive_producer_auth_header = {
    'Authorization': bearer_tokens['executive_producer']
}


#----------------------------------------------------------------------------#
# RBAC Tests I: Missing Authorization | Missing Authentificaton
#   Casting Assistant:
#   - test_error_401_get_all_games (Authorization)
#   Casting Director:
#   - test_error_401_delete_person (Authorization)
#   - test_error_403_delete_person (Authentificaton)
#   Executive Producer:
#   - test_error_401_delete_game (Authorization)
#   - test_error_403_delete_game (Authentificaton)

# RBAC Tests II: Missing Authentificaton (i.e. missing permissions)

#----------------------------------------------------------------------------#

#----------------------------------------------------------------------------#
# Setup of Unittest
#----------------------------------------------------------------------------#

class AgencyTestCase(unittest.TestCase):
    """This class represents the agency test case"""

    def setUp(self):
        """Define test variables and initialize app."""

        self.app = create_app()
        self.client = self.app.test_client
        self.database_path = "postgres://sxvwypvcewiwft:71a5b4af53ca61d9936511c46f96b61fa9d3b9b589f87be97bb49cc98d66aab5@ec2-52-87-58-157.compute-1.amazonaws.com:5432/db28be7l9velkt"
        setup_db(self.app, self.database_path)
        db_drop_and_create_all()
        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
    
    def tearDown(self):
        """Executed after reach test"""
        pass

# Test driven development (TDD): Create testcases first, then add endpoints to pass tests

#----------------------------------------------------------------------------#
# Tests for /persons POST
#----------------------------------------------------------------------------#

    def test_create_new_person(self):
        """Test POST new person."""

        json_create_person = {
            'name' : 'Crisso',
            'age' : 25
        } 

        res = self.client().post('/persons', json = json_create_person, headers = casting_director_auth_header)
        data = json.loads(res.data)
        print(data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['created'], 2)
    
    def test_error_401_new_person(self):
        """Test POST new person w/o Authorization."""

        json_create_person = {
            'name' : 'Crisso',
            'age' : 25
        } 

        res = self.client().post('/persons', json = json_create_person)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 401)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Authorization header is expected.')

    def test_error_422_create_new_person(self):
        """Test Error POST new person."""

        json_create_person_without_name = {
            'age' : 25
        } 

        res = self.client().post('/persons', json = json_create_person_without_name, headers = casting_director_auth_header)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'no name provided.')

#----------------------------------------------------------------------------#
# Tests for /persons GET
#----------------------------------------------------------------------------#

    def test_get_all_persons(self):
        """Test GET all persons."""
        res = self.client().get('/persons?page=1', headers = casting_assistant_auth_header)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertTrue(len(data['persons']) > 0)

    def test_error_401_get_all_persons(self):
        """Test GET all persons w/o Authorization."""
        res = self.client().get('/persons?page=1')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 401)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Authorization header is expected.')

    def test_error_404_get_persons(self):
        """Test Error GET all persons."""
        res = self.client().get('/persons?page=1125125125', headers = casting_assistant_auth_header)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'] , 'no persons found in database.')

#----------------------------------------------------------------------------#
# Tests for /persons PATCH
#----------------------------------------------------------------------------#

    def test_edit_person(self):
        """Test PATCH existing persons"""
        json_edit_person_with_new_age = {
            'age' : 30
        } 
        res = self.client().patch('/persons/1', json = json_edit_person_with_new_age, headers = casting_director_auth_header)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertTrue(len(data['person']) > 0)
        self.assertEqual(data['updated'], 1)

    def test_error_400_edit_person(self):
            """Test PATCH with non json body"""

            res = self.client().patch('/persons/123412', headers = casting_director_auth_header)
            data = json.loads(res.data)

            self.assertEqual(res.status_code, 400)
            self.assertFalse(data['success'])
            self.assertEqual(data['message'] , 'request does not contain a valid JSON body.')

    def test_error_404_edit_person(self):
        """Test PATCH with non valid id"""
        json_edit_person_with_new_age = {
            'age' : 30
        } 
        res = self.client().patch('/persons/123412', json = json_edit_person_with_new_age, headers = casting_director_auth_header)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'] , 'Person with id 123412 not found in database.')

#----------------------------------------------------------------------------#
# Tests for /persons DELETE
#----------------------------------------------------------------------------#

    def test_error_401_delete_person(self):
        """Test DELETE existing person w/o Authorization"""
        res = self.client().delete('/persons/1')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 401)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Authorization header is expected.')

    def test_error_403_delete_person(self):
        """Test DELETE existing person with missing permissions"""
        res = self.client().delete('/persons/1', headers = casting_assistant_auth_header)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 403)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Permission not found.')

    def test_delete_person(self):
        """Test DELETE existing person"""
        res = self.client().delete('/persons/1', headers = casting_director_auth_header)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['deleted'], '1')

    def test_error_404_delete_person(self):
        """Test DELETE non existing person"""
        res = self.client().delete('/persons/15125', headers = casting_director_auth_header)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'] , 'Person with id 15125 not found in database.')

#----------------------------------------------------------------------------#
# Tests for /games POST
#----------------------------------------------------------------------------#

    def test_create_new_game(self):
        """Test POST new game."""

        json_create_game = {
            'title' : 'Crisso Game',
            'release_date' : date.today()
        } 

        res = self.client().post('/games', json = json_create_game, headers = executive_producer_auth_header)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['created'], 2)

    def test_error_422_create_new_game(self):
        """Test Error POST new game."""

        json_create_game_without_name = {
            'release_date' : date.today()
        } 

        res = self.client().post('/games', json = json_create_game_without_name, headers = executive_producer_auth_header)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'no title provided.')

#----------------------------------------------------------------------------#
# Tests for /games GET
#----------------------------------------------------------------------------#

    def test_get_all_games(self):
        """Test GET all games."""
        res = self.client().get('/games?page=1', headers = casting_assistant_auth_header)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertTrue(len(data['games']) > 0)

    def test_error_401_get_all_games(self):
        """Test GET all games w/o Authorization."""
        res = self.client().get('/games?page=1')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 401)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Authorization header is expected.')

    def test_error_404_get_games(self):
        """Test Error GET all games."""
        res = self.client().get('/games?page=1125125125', headers = casting_assistant_auth_header)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'] , 'no games found in database.')

#----------------------------------------------------------------------------#
# Tests for /games PATCH
#----------------------------------------------------------------------------#

    def test_edit_game(self):
        """Test PATCH existing games"""
        json_edit_game = {
            'release_date' : date.today()
        } 
        res = self.client().patch('/games/1', json = json_edit_game, headers = executive_producer_auth_header)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertTrue(len(data['game']) > 0)

    def test_error_400_edit_game(self):
        """Test PATCH with non valid id json body"""
        res = self.client().patch('/games/1', headers = executive_producer_auth_header)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 400)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'] , 'request does not contain a valid JSON body.')

    def test_error_404_edit_game(self):
        """Test PATCH with non valid id"""
        json_edit_game = {
            'release_date' : date.today()
        } 
        res = self.client().patch('/games/123412', json = json_edit_game, headers = executive_producer_auth_header)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'] , 'Game with id 123412 not found in database.')

#----------------------------------------------------------------------------#
# Tests for /games DELETE
#----------------------------------------------------------------------------#

    def test_error_401_delete_game(self):
        """Test DELETE existing game w/o Authorization"""
        res = self.client().delete('/games/1')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 401)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Authorization header is expected.')

    def test_error_403_delete_game(self):
        """Test DELETE existing game with wrong permissions"""
        res = self.client().delete('/games/1', headers = casting_assistant_auth_header)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 403)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Permission not found.')

    def test_delete_game(self):
        """Test DELETE existing game"""
        res = self.client().delete('/games/1', headers = executive_producer_auth_header)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['deleted'], '1')

    def test_error_404_delete_game(self):
        """Test DELETE non existing game"""
        res = self.client().delete('/games/151251', headers = executive_producer_auth_header) 
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'] , 'Game with id 151251 not found in database.')

# Make the tests conveniently executable.
# From app directory, run 'python test_app.py' to start tests
if __name__ == "__main__":
    unittest.main()