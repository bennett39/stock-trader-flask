from config import db
from models import User, Stock, Transaction
from sqlalchemy.sql import func


def select_current_user(user_id):
    """Get the current user SQLAlchemy object."""
    return User.query.filter_by(id=user_id).first()


def select_user_stocks(user):
    """Get list of stocks owned by a given user."""
    return db.session.query(
            func.sum(Transaction.quantity).label('quantity'),
            Stock.name,
            Stock.symbol,
        ).join(User).join(Stock).group_by(
            Transaction.stock_id, Stock, User
        ).filter(User.id==user.id).all()
