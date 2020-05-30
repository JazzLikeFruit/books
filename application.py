"""
Book application
A review website buit with Flask

"""
import os
import requests
from flask import Flask, session, render_template, request, url_for, redirect, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import input_required, length
from flask_bootstrap import Bootstrap
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")
bootstrap = Bootstrap(app)


# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


class loginForm(FlaskForm):
    """ 
    Form class to log user in 
    """
    username = StringField('username', validators=[
                           input_required(), length(min=4, max=15)])
    password = PasswordField('password', validators=[
                             input_required(), length(min=8, max=25)])


class RegisterForm(FlaskForm):
    """ 
    Form class to register user
    """
    username = StringField('username', validators=[
                           input_required(), length(min=4, max=15)])
    password = PasswordField('password', validators=[
                             input_required(), length(min=8, max=25)])


# index page
@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("homepage"))
    else:
        return render_template("index.html")

# Log in page.
@app.route("/login", methods=['GET', 'POST'])
def login():

    # Take user input
    form = loginForm()

    # Check the user input.
    if form.validate_on_submit():
        user = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username": form.username.data}).fetchone()

        # If user found check the pasword and log user in
        if user:
            if check_password_hash(user.password, form.password.data):
                session["user"] = form.username.data
                return redirect(url_for('homepage'))
        return render_template("login.html", error="invalid username/password. Try again.", form=form)

    # Check if already logged in
    if "user" in session:
        return redirect(url_for("homepage"))
    return render_template("login.html", form=form)

# Registration page
@app.route("/registration/", methods=["GET", "POST"])
def registration():

    # Take user input
    form = RegisterForm()

    # Check user input
    if form.validate_on_submit():

        # Check if username in use
        if db.execute("SELECT * FROM users WHERE username =:username",
                      {"username": form.username.data}).fetchone():
            return render_template("registration.html", form=form, error='Username unavailable')

        # Hash pasword
        hashed_password = generate_password_hash(
            form.password.data)

        # Insert input in database
        db.execute(
            "INSERT INTO users (username, password) VALUES (:name, :pass)", {
                "name": form.username.data,
                "pass": hashed_password
            })
        db.commit()
        return redirect(url_for("login"))

    return render_template("registration.html", form=form)


# Home page
@app.route("/homepage/")
def homepage():
    # Check if user is logged in
    if "user" in session:

        # Query a list of 25 books
        books = db.execute("SELECT * FROM books LIMIT 25").fetchall()

        # Return books
        return render_template("homepage.html", books=books)

    else:
        return redirect(url_for("login"))


# Search function
@app.route("/search", methods=["POST"])
def search():
    if "user" in session:

        # User search string
        user_input = request.form.get("name").title()

        # Check if book in database
        if db.execute(
            "select * from books where autor LIKE :name or title LIKE :name or isbn LIKE :name",
                {"name": "%" + user_input + "%"}).rowcount == 0:
            return render_template("error.html", message="No results")

        # Return results
        return render_template("search.html", results=results)
    else:
        return redirect(url_for("login"))


# Seach result page
@app.route("/search/<string:book_isbn>")
def book(book_isbn):
    reviewed = False
    if "user" in session:

        # Check if book exists
        book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {
            "isbn": book_isbn
        }).fetchone()

        # Return error message if book not in database
        if book is None:
            return render_template("error.html", message="Book not found")

        # Query average of reviews
        average = db.execute("SELECT AVG(round(rating)) from reviews where isbn = :isbn", {
            "isbn": book_isbn})

        # Query for book reviews
        reviews = db.execute(
            "SELECT * From reviews where isbn = :isbn", {"isbn": book_isbn}).fetchall()

        # Check if book has reviews
        if db.execute("select * from reviews WHERE isbn = :isbn AND username = :username",
                      {"isbn": book_isbn, "username": session["user"]}).rowcount == 0:

            reviewed = True

        # Query API fot book info
        response = requests.get("https://www.goodreads.com/book/review_counts.json",
                                params={"key": "JBL934ctLhK4oWIBJMKMEA", "isbns": book_isbn})

        # Check response
        if response.status_code != 200:
            raise Exception("ERROR: API request unsuccessful.")
        data = response.json()

        # Gather needed data
        br_rating = data["books"][0]['ratings_count']
        br_average = data["books"][0]['average_rating']
        return render_template("book.html", book=book, reviews=reviews,
                               average_rating=average, reviewed=reviewed, br_rating=br_rating, br_average=br_average)
    else:
        return redirect(url_for("login"))

# Review a book
@app.route("/review/<string:book_isbn>", methods=["POST"])
def review(book_isbn):

    # Insert user review in database
    db.execute("INSERT INTO reviews(username, isbn, text, rating, review_title) VALUES (:username, :isbn, :text, :rating, :review_title)",
               {"username": session["user"],
                "isbn": book_isbn, "text": request.form["text"],
                "rating": request.form["book-rating"],
                "review_title": request.form["review-title"]})
    db.commit()

    return redirect(url_for('book', book_isbn=book_isbn))

# Logout function
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))

# Return details about a book.
@app.route("/api/<string:book_isbn>")
def books_api(book_isbn):

    # Make sure book exists.
    if not db.execute("SELECT * from books WHERE isbn= :isbn",
                      {"isbn": book_isbn}).fetchone():
        return jsonify({"error": "Invalid isbn"}), 422

    # Query for book reviews
    review_info = db.execute(
        "SELECT * from reviews WHERE isbn=:isbn", {"isbn": book_isbn}).rowcount

    # Query for book average
    average_info = db.execute("SELECT AVG(round(rating)) FROM reviews WHERE isbn = :isbn", {
        "isbn": book_isbn}).fetchone()

    # Set average as 0 if book not reviewed
    if average_info[0] == None:
        average_info = 0
    else:
        average_info = average_info[0]

    # Return info in json format
    return jsonify({
        "title": book['title'],
        "author": book['autor'],
        "year": book['publication_year'],
        "isbn": book['isbn'],
        "review_count": int(review_info),
        "average_score": float(average_info)})


if __name__ == '__main__':
    app.run()
