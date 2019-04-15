from config import db
from models import User, Stock, Transaction
from sqlalchemy.sql import func


def delete_transactions_by_user(user_id):
    """ Delete all a user's transactions to reset their portfolio """
    transactions = Transaction.query.filter(
            Transaction.user_id==user_id
            ).all()
    for t in transactions:
        db.session.delete(t)
    db.session.commit()

def insert_stock(symbol, name):
    """ Add a new stock to the database """
    stock = Stock(symbol=symbol, name=name)
    db.session.add(stock)
    db.session.commit()

def insert_transaction(user_id, stock_id, quantity, price):
    """ Add a new transaction (buy or sell) """
    transaction = Transaction(user_id=user_id, stock_id=stock_id,
            quantity=quantity, price=price)
    db.session.add(transaction)
    db.session.commit()

def insert_user(username, password_hash):
    """Create new user"""
    user = User(username=username, password_hash=password_hash)
    db.session.add(user)
    db.session.commit()

def select_user_by_id(user_id):
    """Get user object where id"""
    return User.query.filter_by(id=user_id).first()

def select_user_by_username(username):
    """Get user object where username"""
    return User.query.filter_by(username=username).first()

def select_stock_by_symbol(symbol):
    """Get stock object where symbol"""
    return Stock.query.filter_by(symbol=symbol).first()

def select_stocks_by_user(user_id):
    """Get list of stocks owned by a given user"""
    return (db.session.query(
                func.sum(Transaction.quantity).label('quantity'),
                Stock.name,
                Stock.symbol,
            ).join(User).join(Stock).group_by(
                Transaction.stock_id, Stock, User
            ).filter(User.id==user_id).all())

def select_transactions_by_user(user_id):
    """Get a list of all a user's transactions"""
    return (db.session.query(
                Transaction.id,
                Transaction.quantity,
                Transaction.price,
                Transaction.time,
                Stock.name,
                Stock.symbol,
            ).join(Stock).filter(
                Transaction.user_id==user_id
            ).all())


def select_transactions_by_stock(stock_id, user_id):
    """Get the sum of all a user's transactions of a certain stock"""
    return (db.session.query(
                func.sum(Transaction.quantity).label('shares')
            ).group_by(
                Transaction.stock_id
            ).filter(
                Transaction.stock_id == stock_id,
                Transaction.user_id == user_id
            ).one())

def update_user_cash(change, user_id):
    """ Change user cash after buy or sell """
    user = select_user_by_id(user_id)
    user.cash = user.cash + change
    db.session.commit()

def update_user_hash(new_hash, user_id):
    """ Update the user's password hash on password reset """
    user = select_user_by_id(user_id)
    user.password_hash = new_hash
    db.session.commit()
