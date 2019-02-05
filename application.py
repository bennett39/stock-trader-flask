from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from config import app, db
from helpers import apology, build_portfolio, login_required, lookup, usd
import queries

app.jinja_env.filters['usd'] = usd

@app.route('/')
#  @login_required
def index():
    session['user_id'] = 3 # Remove later

    user = queries.select_current_user(session['user_id'])
    portfolio = build_portfolio(queries.select_user_stocks(user))

    return render_template("portfolio.html", portfolio=portfolio)
