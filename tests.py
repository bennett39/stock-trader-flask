import os
import tempfile
import urllib

from flask_testing import TestCase, LiveServerTestCase
from flask_sqlalchemy import SQLAlchemy
import pytest
from werkzeug.security import check_password_hash, generate_password_hash

from config import create_app
from application import app, db
import helpers as h
import queries as q

class MyTest(TestCase):
    """Complete Flask-Testing test suite"""

    ### Config ###
    def create_app(self):
        """Start new instance of app & initialize db"""
        app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite://"
        app.config['TESTING'] = True
        db.init_app(app)
        return app

    def setUp(self):
        """Create db models in test db"""
        db.create_all()

    def populateTestDb(self):
        """Optional: populate db with test data"""
        user = q.User(
                username="user",
                password_hash="test")
        transaction = q.Transaction(
                user_id=1,
                stock_id=1,
                quantity=1,
                price=1)
        a = q.Stock(
                symbol='AAPL',
                name='Apple')
        b = q.Stock(
                symbol='BIDU',
                name='Baidu')
        db.session.add(user)
        db.session.add(transaction)
        db.session.add(a)
        db.session.add(b)
        db.session.commit()

    def tearDown(self):
        """Clear db between tests"""
        db.session.remove()
        db.drop_all()

    ### queries.py ###
    def test_delete_transaction(self):
        """Deletes all transactions for given user"""
        a = q.Transaction(user_id=1, stock_id=1, quantity=1, price=1)
        b = q.Transaction(user_id=1, stock_id=2, quantity=2, price=2)
        db.session.add(a)
        db.session.add(b)
        db.session.commit()
        q.delete_transactions_by_user(1)
        assert sum(1 for t in q.Transaction.query.all()) == 0

    def test_insert_stock(self):
        """Creates a new stock in database"""
        q.insert_stock('a', 'a')
        assert sum(1 for s in q.Stock.query.all()) == 1

    def test_insert_transaction(self):
        """Creates a new transaction in database"""
        q.insert_transaction(1, 1, 1, 1)
        assert sum(1 for s in q.Transaction.query.all()) == 1

    def test_insert_user(self):
        """Creates a new user in database"""
        q.insert_user('a', 'a')
        assert sum(1 for u in q.User.query.all()) == 1

    def test_select_user_by_id(self):
        """Get a user based on ID"""
        self.populateTestDb()
        assert q.User.query.first() == q.select_user_by_id(1)

    def test_select_user_by_username(self):
        """Get a user by username"""
        self.populateTestDb()
        assert q.User.query.first() == q.select_user_by_username('user')

    def test_select_stock_by_symbol(self):
        """Get a stock by symbol"""
        self.populateTestDb()
        assert q.Stock.query.first() == q.select_stock_by_symbol('AAPL')

    def test_select_stocks_by_user(self):
        """Get a sum of user's stocks"""
        self.populateTestDb()
        assert (1.0, 'Apple', 'AAPL') in q.select_stocks_by_user(1)

    def test_select_transactions_by_user(self):
        """Get a user's transactions"""
        self.populateTestDb()
        assert 'AAPL' in q.select_transactions_by_user(1)[0]

    def test_select_transactions_by_stock(self):
        """Get sum of users transactions of a stock"""
        self.populateTestDb()
        assert sum(q.select_transactions_by_stock(1, 1)) == 1

    def test_update_user_cash(self):
        """Add amount to user cash"""
        self.populateTestDb()
        q.update_user_cash(999, 1)
        assert q.User.query.first().cash == 10999

    def test_update_user_hash(self):
        """Update user's password hash"""
        self.populateTestDb()
        q.update_user_hash('baz', 1)
        assert q.User.query.first().password_hash == 'baz'


    ### models.py ###
    def test_user_repr(self):
        """Test __repr__ in User model"""
        assert repr(
                q.User(
                    username='foo',
                    password_hash='bar')
                ) == "<User foo>"

    def test_stock_repr(self):
        """Test __repr__ in Stock model"""
        assert repr(
                q.Stock(
                    symbol='foo',
                    name='bar')
                ) == "<Stock foo>"

    def test_transaction_repr(self):
        """Test __repr__ in Transaction model"""
        self.populateTestDb()
        assert (repr(q.Transaction.query.first())
                == "<Transaction <User user>: <Stock AAPL>>")


    ### helpers.py ###
    def test_build_history(self):
        """Create dictionary from user transaction history"""
        self.populateTestDb()
        history = h.build_history(q.select_transactions_by_user(1))
        assert 'name' in history[1]
        assert 'price' in history[1]
        assert 'time' in history[1]

    def test_build_portfolio(self):
        """Create portfolio w/ current prices from user stocks"""
        self.populateTestDb()
        portfolio = h.build_portfolio(
                q.select_stocks_by_user(1),
                9999
                )
        assert 'stocks' in portfolio
        assert 'AAPL' in portfolio['stocks']
        assert 'name' in portfolio['stocks']['AAPL']
        assert 'value' in portfolio['stocks']['AAPL']
        assert 'cash' in portfolio
        assert 'total' in portfolio

    def test_usd(self):
        """Format value as USD string"""
        assert h.usd(800) == "$800.00"
        assert h.usd(0) == "$0.00"
        assert h.usd(9.99) == "$9.99"

    def test_login_page(self):
        response = self.client.get('/login')
        assert b'Log In' in response.data

    def test_register_page(self):
        response = self.client.get('/register')
        assert b'Create a New Account' in response.data


#  @pytest.fixture
#  def client():
    #  db_fd, app.config['database'] = tempfile.mkstemp()
    #  app.config['testing'] = true
    #  client = app.test_client()

    #  with app.app_context():
        #  db.init_app(app)

    #  yield client

    #  os.close(db_fd)
    #  os.unlink(app.config['database'])

#  def test_login_get(client):
    #  assert b'Log In' in client.get('/login').data

#  def test_register_get(client):
    #  assert b'create a new account' in client.get('/register').data

#  # todo - test login

#  def logout(client):
    #  return client.get('/logout', follow_redirects=true)

#  def test_logout(client):
    #  assert b'Log In' in logout(client).data

#  ### helpers.py ###
#  # TODO - test apology, login_required w/ client-side render_template

#  ### config.py ###
#  # TODO - test after_request with http client

#  ### aplication.py ###
#  # TODO - Test all routes with HTTP client
