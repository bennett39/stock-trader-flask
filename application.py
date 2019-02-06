from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from config import app, db
from helpers import apology, build_portfolio, login_required, lookup, usd
import queries as q

app.jinja_env.filters['usd'] = usd

@app.route('/')
@login_required
def index():
    """Show portfolio of user's stocks"""
    user = q.select_user_by_id(session['user_id'])
    portfolio = build_portfolio(q.select_stocks_by_user(user), user.cash)

    return render_template("index.html", portfolio=portfolio)


@app.route('/login', methods=['GET','POST'])
def login():
    """Log user in"""
    session.clear()

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username: return apology("Must provide username")
        elif not password: return apology("Must provide password")

        user = q.select_user_by_username(username) 
        try: 
            if check_password_hash(user.password_hash, password):
                session['user_id'] = user.id
                return redirect('/')
            else: return apology("Incorrect password")
        except AttributeError: return apology("No such user")
        
    else: # via 'GET'
        return render_template("login.html")


@app.route('/logout')
def logout():
    """Log user out"""
    session.clear()
    return redirect('/login')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register user"""
    session.clear()

    if request.method == 'POST':
        username, password, confirmation = (
                request.form.get('username'), 
                request.form.get('password'),
                request.form.get('confirmation')
            )

        if not username: return apology("Missing username")
        elif not password: return apology("Missing password")
        elif not confirmation: return apology("Missing confirmation")
        elif password != confirmation: 
            return apology("Password doesn't match confirmation")

        password_hash = generate_password_hash(password)
        
        try: 
            q.insert_user(username, password_hash)
        except Exception:
            return apology("Username already exists")

        session['user_id'] = q.select_user_by_username(username).id

        return redirect('/')

    else:
        return render_template("register.html")
