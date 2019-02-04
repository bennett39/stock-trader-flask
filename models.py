from application import db
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False) 
    password_hash = db.Column(db.String(120), nullable=False)
    cash = db.Column(db.Float, default=10000.00)
    transactions = db.relationship('Transaction', cascade='all,delete',
            backref='user')

    def __repr__(self):
        return f'<User {self.username}>'


class Stock(db.Model):
    __tablename__ = 'stock'
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(80), unique=True, nullable=False)
    transactions = db.relationship('Transaction', cascade='all,delete',
            backref='stock')

    def __repr__(self):
        return f'<Stock {self.symbol}>'


class Transaction(db.Model):
    __tablename__ = 'transaction'
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, 
        db.ForeignKey('user.id', ondelete='CASCADE'), 
        nullable=False)

    stock_id = db.Column(db.Integer, 
        db.ForeignKey('stock.id', ondelete='CASCADE'), 
        nullable=False)

    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    time = db.Column(db.DateTime, nullable=False,
        default=datetime.utcnow)

    def __repr__(self):
        return f'<Transaction {self.user}: {self.stock}>'
