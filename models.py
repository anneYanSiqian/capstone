import os
from sqlalchemy import Column, String, Integer, create_engine, Date, Float
from flask_sqlalchemy import SQLAlchemy
import json
from datetime import date

#----------------------------------------------------------------------------#
# Database Setup 
#----------------------------------------------------------------------------#

# Use Production Database.
# If run locally, key does not exist, so use locally set database instead.
database_path = "postgres://sxvwypvcewiwft:71a5b4af53ca61d9936511c46f96b61fa9d3b9b589f87be97bb49cc98d66aab5@ec2-52-87-58-157.compute-1.amazonaws.com:5432/db28be7l9velkt"

db = SQLAlchemy()

def setup_db(app, database_path=database_path):
    '''binds a flask application and a SQLAlchemy service'''
    app.config["SQLALCHEMY_DATABASE_URI"] = database_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.app = app
    db.init_app(app)
    db.create_all()

def db_drop_and_create_all():
    '''drops the database tables and starts fresh
    can be used to initialize a clean database
    '''
    db.drop_all()
    db.create_all()
    db_init_records()

def db_init_records():
    '''this will initialize the database with some test records.'''

    new_person = (Person(
        name = 'Matthew',
        gender = 'Male',
        age = 25
    ))

    new_game = (Game(
        title = 'Matthew first Game',
        release_date = date.today()
    ))

    new_performance = Performance.insert().values(
        Game_id = new_game.id,
        Person_id = new_person.id,
        person_fee = 500.00
    )

    new_person.insert()
    new_game.insert()
    db.session.execute(new_performance) 
    db.session.commit()

#----------------------------------------------------------------------------#
# Performance Junction Object N:N 
#----------------------------------------------------------------------------#

# Instead of creating a new Table, the documentation recommends to create a association table
Performance = db.Table('Performance', db.Model.metadata,
    db.Column('Game_id', db.Integer, db.ForeignKey('games.id')),
    db.Column('Person_id', db.Integer, db.ForeignKey('persons.id')),
    db.Column('person_fee', db.Float)
)

#----------------------------------------------------------------------------#
# Persons Model 
#----------------------------------------------------------------------------#

class Person(db.Model):  
  __tablename__ = 'persons'

  id = Column(Integer, primary_key=True)
  name = Column(String)
  gender = Column(String)
  age = Column(Integer)

  def __init__(self, name, gender, age):
    self.name = name
    self.gender = gender
    self.age = age

  def insert(self):
    db.session.add(self)
    db.session.commit()
  
  def update(self):
    db.session.commit()

  def delete(self):
    db.session.delete(self)
    db.session.commit()

  def format(self):
    return {
      'id': self.id,
      'name' : self.name,
      'gender': self.gender,
      'age': self.age
    }

#----------------------------------------------------------------------------#
# Games Model 
#----------------------------------------------------------------------------#

class Game(db.Model):  
  __tablename__ = 'games'

  id = Column(Integer, primary_key=True)
  title = Column(String)
  release_date = Column(Date)
  persons = db.relationship('Person', secondary=Performance, backref=db.backref('performances', lazy='joined'))

  def __init__(self, title, release_date) :
    self.title = title
    self.release_date = release_date

  def insert(self):
    db.session.add(self)
    db.session.commit()
  
  def update(self):
    db.session.commit()

  def delete(self):
    db.session.delete(self)
    db.session.commit()

  def format(self):
    return {
      'id': self.id,
      'title' : self.title,
      'release_date': self.release_date
    }