import urllib
from flask_testing import TestCase
from flask_sqlalchemy import SQLAlchemy

from config import create_app, db
import queries as q

class MyTest(TestCase):
    def create_app(self):
        app = create_app("sqlite://")
        app.config['TESTING'] = True
        db.init_app(app)
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_db_connection(self):
        """Create an instance of all models and add to db"""
        user = q.User(
                username="test", 
                password_hash="test"
                )
        transaction = q.Transaction(
                user_id=1,
                stock_id=1,
                quantity=1,
                price=1
                )
        stock = q.Stock(
                symbol='a',
                name='a'
                )
        db.session.add(user)
        db.session.add(transaction)
        db.session.add(stock)
        db.session.commit()
        assert user in db.session

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

    def test_select_user_id(self):
        a = q.User(username='a', password_hash='a')
        db.session.add(a)
        db.session.commit()
        a = q.User.query.first()
        assert a == q.select_user_by_id(a.id)
