import os

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, \
                    ForeignKey
from sqlalchemy import inspect

from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

engine = create_engine(os.environ['DATABASE_URL'])
db = engine.connect()
#  db = SQL("sqlite:///finance.db")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # Create portfolio dict
    portfolio = db.execute("""SELECT txs.stock_id, sum(quantity), price, symbol, name
                            FROM txs
                            INNER JOIN stocks ON stocks.stock_id = txs.stock_id
                            WHERE txs.u_id = :u_id
                            GROUP BY txs.stock_id
                            HAVING sum(quantity) > 0""",
                           u_id=session["user_id"])

    # Get user's cash balance
    cash = db.execute("SELECT cash FROM users WHERE id = :u_id", u_id=session["user_id"])

    # Create a running total of all user's assets
    total = cash[0]["cash"]

    # Lookup current stock prices
    for i in portfolio:
        # Get current price of stock
        quote = lookup(i["symbol"])

        # Create dict items for current price and present value of assets
        i["current"] = usd(quote["price"])
        i["pvalue"] = usd(quote["price"] * float(i["sum(quantity)"]))

        change = (float(quote["price"]) - float(i["price"])) / float(i["price"])
        i["change"] = "{0:.0%}".format(change)

        i["price"] = usd(i["price"])

        # Add present value of asset to user's total value
        total = total + float(quote["price"]) * float(i["sum(quantity)"])

    if not portfolio:
        portfolio = [{"name": "Buy some stocks and they'll appear here!"}]

    # Pass in the portfolio object, cash balance, and total when rendering
    return render_template("index.html", portfolio=portfolio, cash=usd(cash[0]["cash"]), total=usd(total))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Did user enter a symbol?
        if not request.form.get("symbol"):
            return apology("Provide a symbol", 400)

        # Did user enter a quantity?
        elif not request.form.get("shares").isdigit():
            return apology("Provide a valid quantity", 400)

        # Lookup symbol and save price
        quote = lookup(request.form.get("symbol"))

        # If lookup fails, return error
        if not quote:
            return apology("No such company", 400)

        # Total of buy order
        quantity = request.form.get("shares", type=int)
        total = float(quote["price"]) * float(quantity)

        # Get user cash balance from database
        cash = db.execute("SELECT cash FROM users WHERE id = :u_id",
                          u_id=session["user_id"])

        # If user has the cash to make the purchase
        if total < cash[0]["cash"]:

            # Check for stock in stocks table, create it if not there
            stock_id = db.execute("SELECT stock_id FROM stocks WHERE symbol = :symbol", symbol=quote["symbol"])

            if not stock_id:
                db.execute("INSERT INTO stocks (symbol, name) VALUES (:symbol, :name)",
                           symbol=quote["symbol"],
                           name=quote["name"])

                stock_id = db.execute("SELECT stock_id FROM stocks WHERE symbol = :symbol", symbol=quote["symbol"])

            # Create transaction in txs table
            db.execute("INSERT INTO txs (stock_id, quantity, price, u_id) \
                    VALUES(:stock_id, :quantity, :price, :u_id)",
                       stock_id=stock_id[0]["stock_id"], quantity=quantity,
                       price=quote["price"], u_id=session["user_id"])

            # Subtract total from cash
            db.execute("UPDATE users SET cash = cash - :total WHERE id = :u_id",
                       total=total,
                       u_id=session["user_id"])

            # return render_template("buy.html", message="Successfully bought " + str(quantity) + " shares of " \
            #                                    + str(quote["name"]) + " (" + str(quote["symbol"]) \
            #                                    + ") for " + str(usd(total)))

            return redirect("/")

        # User doesn't have enough cash
        else:
            return apology("Not enough cash", 400)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # Create history dict
    history = db.execute("""SELECT txs.stock_id, quantity, price, time, symbol, name
                            FROM txs
                            INNER JOIN stocks ON stocks.stock_id = txs.stock_id
                            WHERE u_id = :u_id""",
                         u_id=session["user_id"])

    # Add & update fields in history dict
    for i in history:
        if int(i["quantity"]) < 0:
            i["type"] = "Sell"
        else:
            i["type"] = "Buy"
        i["total"] = usd((float(i["price"]) * float(i["quantity"])))
        i["price"] = usd(i["price"])

    # Render html and pass in history dict
    return render_template("history.html", history=history)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/nuke", methods=["GET", "POST"])
@login_required
def nuke():

    # Arriving via POST
    if request.method == "POST":

        # Check for blank or "no" form response
        if not request.form.get("yesno") or request.form.get("yesno") == "no":
            return apology("OK, we won't reset your portfolio", 403)

        if request.form.get("yesno") == "yes":
            db.execute("DELETE FROM txs WHERE u_id = :u_id", u_id=session["user_id"])
            db.execute("UPDATE users SET cash = 10000 WHERE id = :u_id", u_id=session["user_id"])

        return redirect("/")

    # Arriving via GET
    else:
        redirect("/profile")


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    # Arriving via POST - form submission
    if request.method == "POST":

        # Check if form inputs are blank
        if not request.form.get("password") or not request.form.get("new") or not request.form.get("confirmation"):
            return apology("Fill out all fields", 403)

        # Check if new password and confirmation match
        elif request.form.get("new") != request.form.get("confirmation"):
            return apology("New password and confirmation don't match")

        # Query database for user info
        rows = db.execute("SELECT * FROM users WHERE id = :u_id",
                          u_id=session["user_id"])

        # Check current password hash
        if check_password_hash(rows[0]["hash"], request.form.get("password")):

            # Hash new password
            hash = generate_password_hash(request.form.get("new"))

            # Update users table in database
            db.execute("UPDATE users SET hash = :hash WHERE id = :u_id",
                       hash=hash, u_id=session["user_id"])

            return render_template("profile.html", profile=rows, message="Successfully updated password!")

        else:
            return apology("Incorrect password", 403)

    # Arriving via GET
    else:
        # Get user information
        profile = db.execute("SELECT * FROM users WHERE id = :u_id",
                             u_id=session["user_id"])
        profile[0]["cash"] = usd(profile[0]["cash"])

        return render_template("profile.html", profile=profile)


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Use lookup from helpers.py to get quote
        quote = lookup(request.form.get("symbol"))

        # If company doesn't exist
        if not quote:
            return apology("Company doesn't exist.", 400)

        # Render quoted.html on success & pass variables
        return render_template("quoted.html", name=quote["name"], symbol=quote["symbol"], price=usd(quote["price"]))

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("Missing username!", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("Missing password!", 400)

        # Ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("Missing password confirmation!", 400)

        # Check match between password and confirmation
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("Password and confirmation don't match :(", 400)

        # Hash the password
        hash = generate_password_hash(request.form.get("password"))

        # Add username to database
        result = db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)",
                            username=request.form.get("username"),
                            hash=hash)

        # Apologize if username already exists
        if not result:
            return apology("Username already exists", 400)

        # Start session with new user id
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Did user enter a symbol?
        if not request.form.get("symbol"):
            return apology("Provide a symbol", 400)

        # Did user enter a quantity?
        elif not request.form.get("shares").isdigit():
            return apology("Provide a valid quantity", 400)

        # Lookup symbol and save price
        quote = lookup(request.form.get("symbol"))

        # If lookup fails, return error
        if not quote:
            return apology("No such company", 400)

        # Get stock id
        stock_id = db.execute("SELECT stock_id FROM stocks WHERE symbol = :symbol",
                              symbol=quote["symbol"])
        position = db.execute("""SELECT sum(quantity)
                                FROM txs
                                WHERE u_id = :u_id AND stock_id = :stock_id
                                GROUP BY stock_id""",
                              u_id=session["user_id"],
                              stock_id=stock_id[0]["stock_id"])
        quantity = request.form.get("shares", type=int)

        if not stock_id or not position:
            return apology("You don't own that stock", 400)

        # Check if user owns that stock AND if sell amount <= quantity owned
        if position[0]["sum(quantity)"] >= quantity:

            # Calculate transaction total
            total = quantity * float(quote["price"])

            # Add sale to txs table
            db.execute("INSERT INTO txs (stock_id, quantity, price, u_id) \
                    VALUES(:stock_id, :quantity, :price, :u_id)",
                       stock_id=stock_id[0]["stock_id"], quantity=-1 * quantity,
                       price=quote["price"], u_id=session["user_id"])

            # Update cash in users table
            db.execute("UPDATE users SET cash = cash + :total WHERE id = :u_id",
                       total=total,
                       u_id=session["user_id"])

            # return render_template("sell.html", message="Successfully sold " + str(quantity) + " shares of " \
            #                                    + str(quote["name"]) + " (" + str(quote["symbol"]) \
            #                                    + ") for " + str(usd(total)))

            return redirect("/")

        # Else, render apology
        else:
            return apology("You don't own enough of that stock for this sell order", 400)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        portfolio = db.execute("""SELECT txs.stock_id, sum(quantity), symbol
                            FROM txs
                            INNER JOIN stocks ON stocks.stock_id = txs.stock_id
                            WHERE txs.u_id = :u_id
                            GROUP BY txs.stock_id
                            HAVING sum(quantity) > 0""",
                               u_id=session["user_id"])

        return render_template("sell.html", portfolio=portfolio)


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

db.close()
