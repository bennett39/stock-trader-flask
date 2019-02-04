from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from config import app, db
from models import User, Stock, Transaction

session['user_id'] = 3 # Remove later

@app.route('/')
#  @login_required
def index():
    user = User.query.filter_by(id=session['user_id']).first()

    portfolio = db.session.query(
            Transaction.stock_id, 
            func.sum(Transaction.quantity).label('total'),
            Stock.name,
            Stock.symbol,
            User.username
        ).join(User).join(Stock).group_by(
            Transaction.stock_id, Stock, User
        ).filter(User.id==user.id).all()

    return portfolio
