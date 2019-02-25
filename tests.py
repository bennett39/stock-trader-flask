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

    def populateTestDb(self):
        user = q.User(
                username="user", 
                password_hash="test"
                )
        transaction = q.Transaction(
                user_id=1,
                stock_id=1,
                quantity=1,
                price=1
                )
        a = q.Stock(
                symbol='aaa',
                name='aaa'
                )
        b = q.Stock(
                symbol='bbb',
                name='bbb'
                )
        db.session.add(user)
        db.session.add(transaction)
        db.session.add(a)
        db.session.add(b)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()


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
        assert q.Stock.query.first() == q.select_stock_by_symbol('aaa')

    def test_select_stocks_by_user(self):
        """Get a sum of user's stocks"""
        self.populateTestDb()
        assert (1.0, 'aaa', 'aaa') in q.select_stocks_by_user(1)

    def test_select_transactions_by_user(self):
        """Get a user's transactions"""
        self.populateTestDb()
        assert 'aaa' in q.select_transactions_by_user(1)[0]

    def test_select_transactions_by_stock(self):
        """Get sum of users transactions of a stock"""
        self.populateTestDb()
        assert sum(q.select_transactions_by_stock(1, 1)) == 1

