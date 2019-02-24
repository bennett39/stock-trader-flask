import os

from dotenv import load_dotenv
from flask import Flask
from flask_heroku import Heroku
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

def create_app(db_uri):
    app = Flask( __name__ )
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.secret_key = os.getenv('SECRET_KEY').encode('utf-8')
    return app

app = create_app(os.getenv('DATABASE_URL'))

db = SQLAlchemy()
db.init_app(app)

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

heroku = Heroku(app)
