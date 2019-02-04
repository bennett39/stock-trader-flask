import os

from dotenv import load_dotenv
from flask import Flask
from flask_heroku import Heroku
from flask_sqlalchemy import SQLAlchemy

load_dotenv()
app = Flask( __name__ )
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
heroku = Heroku(app)
db = SQLAlchemy(app)
