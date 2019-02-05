from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from config import app, db
from helpers import apology, login_required, lookup, usd
from models import User, Stock, Transaction

app.jinja_env.filters['usd'] = usd

@app.route('/')
#  @login_required
def index():
    session['user_id'] = 3 # Remove later

    user = User.query.filter_by(id=session['user_id']).first()
    portfolio = build_portfolio(query_user_stocks(user))

    return render_template("portfolio.html", portfolio=portfolio)


def build_portfolio(stocks)
    portfolio = {}
    for stock in stocks:
        price = lookup(stock.symbol)
        portfolio[stock.symbol] = {
            'name': stock.name,
            'quantity': stock.quantity,
            'price': usd(price),
            'total': usd(stock.quantity * price), 
        }
    return portfolio


def query_user_stocks(user):
    return db.session.query(
            func.sum(Transaction.quantity).label('quantity'),
            Stock.name,
            Stock.symbol,
        ).join(User).join(Stock).group_by(
            Transaction.stock_id, Stock, User
        ).filter(User.id==user.id).all()
