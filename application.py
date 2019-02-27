from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from config import app, db
from stocks import stocks
import helpers as h
import queries as q

app.jinja_env.filters['usd'] = h.usd
login_required = h.login_required

@app.route('/')
@login_required
def index():
    """Show portfolio of user's stocks"""
    user = q.select_user_by_id(session['user_id'])
    portfolio = h.build_portfolio(
            q.select_stocks_by_user(user.id),
            user.cash)

    return render_template("index.html", portfolio=portfolio,
            stocks=stocks)


@app.route('/buy', methods=['GET', 'POST'])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == 'POST':
        symbol = request.form.get('symbol')
        shares= request.form.get('shares')

        if not symbol:
            return h.apology("Provide a symbol")
        elif not shares.isdigit():
            return h.apology("Provide a valid quantity")

        quote = h.lookup(symbol)
        if not quote:
            return h.apology("No such company")

        order_total = float(shares) * float(quote['price'])
        user = q.select_user_by_id(session['user_id'])

        if order_total <= user.cash:
            stock = q.select_stock_by_symbol(quote['symbol'])
            try: stock.id
            except AttributeError:
                q.insert_stock(quote['symbol'], quote['name'])
                stock = q.select_stock_by_symbol(quote['symbol'])
            q.insert_transaction(
                    session['user_id'],
                    stock.id,
                    shares,
                    quote['price']
                    )
            q.update_user_cash(order_total*-1, session['user_id'])
            return redirect('/')
        return h.apology("Not enough cash")
    else:
        return render_template('buy.html', stocks=stocks)


@app.route('/history')
@login_required
def history():
    """Show history of transactions"""
    history = dict(sorted(
        h.build_history(
            q.select_transactions_by_user(
                session['user_id']
            )).items()
        ))
    return render_template('history.html', history=history)


@app.route('/login', methods=['GET','POST'])
def login():
    """Log user in"""
    session.clear()

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username: return h.apology("Must provide username")
        elif not password: return h.apology("Must provide password")

        user = q.select_user_by_username(username)
        try:
            if check_password_hash(user.password_hash, password):
                session['user_id'] = user.id
                return redirect('/')
            else:
                return h.apology("Incorrect password")
        except AttributeError:
            return h.apology("No such user")
    else:
        return render_template("login.html")


@app.route('/logout')
def logout():
    """Log user out"""
    session.clear()
    return redirect('/login')


@app.route('/nuke', methods=['GET', 'POST'])
@login_required
def nuke():
    """Reset user portfolio"""
    if request.method == 'POST':
        confirm = request.form.get('yesno')
        if not confirm or confirm == 'no':
            return h.apology("Ok, we won't reset your portfolio")
        if confirm == 'yes':
            q.delete_transactions_by_user(session['user_id'])
            user = q.select_user_by_id(session['user_id'])
            q.update_user_cash(10000-user.cash, session['user_id'])
        return redirect('/')
    return redirect('/profile')


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Show user profile information"""
    if request.method == 'POST':
        password = request.form.get('password')
        new_password = request.form.get('new')
        confirmation = request.form.get('confirmation')
        if not password or not new_password or not confirmation:
            return h.apology("Please fill all fields")
        elif new_password != confirmation:
            return h.apology("New password and confirmation don't match")

        user = q.select_user_by_id(session['user_id'])
        if check_password_hash(user.password_hash, password):
            new_hash = generate_password_hash(new_password)
            q.update_user_hash(new_hash, session['user_id'])
            return redirect('/login')
        else:
            return h.apology("Incorrect password")
    else:
        user = q.select_user_by_id(session['user_id'])
        user.cash = h.usd(user.cash)
        return render_template('profile.html', user=user)


@app.route('/quote', methods=['GET', 'POST'])
@login_required
def quote():
    """Get stock quote"""
    if request.method == 'POST':
        quote = h.lookup(request.form.get('symbol'))
        if not quote:
            return h.apology("Company doesn't exist.")
        return render_template(
                'quoted.html',
                symbol=quote['symbol'],
                price=quote['price'],
                name=quote['name']
                )
    else:
        return render_template('quote.html', stocks=stocks)


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

        if not username:
            return h.apology("Missing username")
        elif not password:
            return h.apology("Missing password")
        elif not confirmation:
            return h.apology("Missing confirmation")
        elif password != confirmation:
            return h.apology("Password doesn't match confirmation")

        password_hash = generate_password_hash(password)

        try:
            q.insert_user(username, password_hash)
        except Exception:
            return h.apology("Username already exists")

        session['user_id'] = q.select_user_by_username(username).id

        return redirect('/')

    return render_template("register.html")


@app.route('/sell', methods=['GET', 'POST'])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == 'POST':
        symbol = request.form.get('symbol')
        shares = request.form.get('shares')
        if not symbol:
            return h.apology("Provide a symbol")
        elif not shares.isdigit():
            return h.apology("Provide a valid quantity")
        shares = float(shares)
        quote = h.lookup(symbol)
        if not quote:
            return h.apology("No such company")
        stock = q.select_stock_by_symbol(symbol)
        position = q.select_transactions_by_stock(
                stock.id,
                session['user_id'])
        try:
            stock.id
            position.shares
        except AttributeError:
            return h.apology("You don't own that stock")
        if position.shares >= shares:
            order_total = shares * quote['price']
            q.insert_transaction(
                    session['user_id'],
                    stock.id,
                    shares*-1,
                    quote['price'])
            q.update_user_cash(order_total, session['user_id'])
            return redirect('/')
        else:
            return h.apology("You don't own enough of that stock.")
    else:
        user = q.select_user_by_id(session['user_id'])
        return render_template('sell.html',
                portfolio=h.build_portfolio(
                    q.select_stocks_by_user(user.id),
                    user.cash)
                )
