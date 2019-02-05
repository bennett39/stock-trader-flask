from config import db
from models import User, Stock, Transaction
from sqlalchemy.sql import func

def insert_user(username, password_hash):
    """Create new user"""
    user = User(username=username, password_hash=password_hash)
    db.session.add(user)
    db.session.commit()

def select_user_by_id(user_id):
    """Get user object."""
    return User.query.filter_by(id=user_id).first()

def select_user_by_username(username):
    """Get user object."""
    return User.query.filter_by(username=username).first()

def select_stocks_by_user(user):
    """Get list of stocks owned by a given user."""
    return db.session.query(
            func.sum(Transaction.quantity).label('quantity'),
            Stock.name,
            Stock.symbol,
        ).join(User).join(Stock).group_by(
            Transaction.stock_id, Stock, User
        ).filter(User.id==user.id).all()
