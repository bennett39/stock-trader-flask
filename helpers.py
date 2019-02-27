import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps


def apology(error, code=400):
    """Render error as an apology to user."""
    return render_template("apology.html", error=error, code=code)


def build_history(transactions):
    history = {}
    for transaction in transactions:
        history[transaction.id] = {
                'name': transaction.name,
                'symbol': transaction.symbol,
                'quantity': transaction.quantity,
                'price': usd(transaction.price),
                'type': 'Sell' if transaction.quantity < 0 else 'Buy',
                'total': usd(transaction.price * transaction.quantity),
                'time': transaction.time
        }
    return history


def build_portfolio(stocks, cash):
    """Build portfolio of current stock values."""
    portfolio = {
        'stocks': {},
        'cash': usd(cash),
        'total': cash
    }
    for stock in stocks:
        if stock.quantity <= 0:
            portfolio['stocks'].pop(stock, None)
        else:
            price = lookup(stock.symbol)['price']
            value = stock.quantity * price
            portfolio['stocks'][stock.symbol] = {
                'name': stock.name,
                'quantity': stock.quantity,
                'price': usd(price),
                'value': usd(value),
            }
            portfolio['total'] += value
    portfolio['total'] = usd(portfolio['total'])
    return portfolio


def login_required(f):
    """
    Decorate routes to require login.
    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """
    Look up a quote for a stock symbol.
    https://iextrading.com/developer/docs/
    """

    # Contact API
    try:
        response = requests.get(f"https://api.iextrading.com/1.0/stock/{urllib.parse.quote_plus(symbol)}/quote")
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        return {
            'name': quote['companyName'],
            'price': float(quote['latestPrice']),
            'symbol': quote['symbol']
        }
    except (KeyError, TypeError, ValueError):
        return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
