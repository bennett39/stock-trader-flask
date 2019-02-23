import urllib
from flask_testing import TestCase

from config import create_app, db
from queries import User, Transaction, Stock

class MyTest(TestCase):
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True

    def create_app(self):
        app = create_app()
        db.init_app(app)
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_db_connection(self):
        user = User(username="test", password_hash="test")
        db.session.add(user)
        db.session.commit()
        assert user in db.session
