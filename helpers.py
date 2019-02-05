import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps


def apology(error, code=400):
    """Render error as an apology to user."""
    return render_template("apology.html", error=error, code=code)


def build_portfolio(stocks):
    """Build portfolio of current stock values."""
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
        return float(quote["latestPrice"])
    except (KeyError, TypeError, ValueError):
        return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
