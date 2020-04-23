import os
import requests
from flask import Flask, session, render_template, request, url_for, redirect, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import input_required, length
from flask_bootstrap import Bootstrap
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.config['SECRET_KEY'] = 'thiskeyissupposedtobesecret!'
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
    username = StringField('username', validators=[
                           input_required(), length(min=4, max=15)])
    password = PasswordField('password', validators=[
                             input_required(), length(min=8, max=25)])


class RegisterForm(FlaskForm):
    username = StringField('username', validators=[
                           input_required(), length(min=4, max=15)])
    password = PasswordField('password', validators=[
                             input_required(), length(min=8, max=25)])


# Log in page
@app.route("/")
def index():

    return render_template("index.html")


@app.route("/login", methods=['GET', 'POST'])
def login():
    error = ''
    form = loginForm()
    if form.validate_on_submit():
        user = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username": form.username.data}).fetchone()
        if user:
            if check_password_hash(user.password, form.password.data):
                session["user"] = form.username.data
                return redirect(url_for('homepage'))
        error = "invalid username/password. Try again."
        return render_template("login.html", error=error, form=form)
    if "user" in session:
        return redirect(url_for("homepage"))
    return render_template("login.html", form=form)

# Registration page
@app.route("/registration/", methods=["GET", "POST"])
def registration():
    error = ''
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(
            form.password.data, method='sha256')

        db.execute(
            "INSERT INTO users (username, password) VALUES (:name, :pass)", {
                "name": form.username.data,
                "pass": hashed_password
            })
        db.commit()
        error = 'Username added'
        return render_template("registration.html", form=form, error=error)

    return render_template("registration.html", form=form)


# Home page
@app.route("/homepage/")
def homepage():
    if "user" in session:
        books = db.execute("SELECT * FROM books LIMIT 25").fetchall()
        return render_template("homepage.html", books=books)
    else:
        return redirect(url_for("login"))


# search function
@app.route("/search", methods=["POST"])
def search():
    if "user" in session:
        name = request.form.get("name").title()
        results = db.execute(
            "select * from books where autor LIKE :name or title LIKE :name or isbn LIKE :name",
            {"name": "%" + name + "%"})
        if results.rowcount == 0:
            return render_template("error.html", message="No results")
        return render_template("search.html", results=results)
    else:
        return redirect(url_for("login"))


# Seach result page
@app.route("/search/<string:book_isbn>")
def book(book_isbn):
    reviewed = False

    if "user" in session:

        book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {
            "isbn": book_isbn
        }).fetchone()

        if book is None:
            return render_template("error.html", message="Book not found")

        average = db.execute("SELECT AVG(round(rating)) from reviews where isbn = :isbn", {
            "isbn": book_isbn}).fetchone()
        reviews = db.execute(
            "SELECT * From reviews where isbn = :isbn", {"isbn": book_isbn}).fetchall()

        review_made = db.execute("select * from reviews WHERE isbn = :isbn AND username = :username",
                                 {"isbn": book_isbn, "username": session["user"]}).rowcount

        if review_made == 0:
            reviewed = True

        res = requests.get("https://www.goodreads.com/book/review_counts.json",
                           params={"key": "JBL934ctLhK4oWIBJMKMEA", "isbns": book_isbn})
        if res.status_code != 200:
            raise Exception("ERROR: API request unsuccessful.")
        data = res.json()
        br_rating = data["books"][0]['ratings_count']
        br_average = data["books"][0]['average_rating']
        return render_template("book.html", book=book, reviews=reviews,
                               average_rating=average, reviewed=reviewed, br_rating=br_rating, br_average=br_average)

    else:
        return redirect(url_for("login"))


@app.route("/review/<string:book_isbn>", methods=["POST"])
def review(book_isbn):
    if request.method == "POST":
        review_title = request.form["review-title"]
        text = request.form["text"]
        book_rating = request.form["book-rating"]

        db.execute("INSERT INTO reviews(username, isbn, text, rating, review_title) VALUES (:username, :isbn, :text, :rating, :review_title)",
                   {"username": session["user"], "isbn": book_isbn, "text": text, "rating": book_rating, "review_title": review_title})
        db.commit()
        return redirect(url_for('book', book_isbn=book_isbn))


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


@app.route("/api/books/<string:book_isbn>")
def books_api(book_isbn):
    """Return details about a book."""

    # Make sure book exists.
    book = db.execute("SELECT * from books WHERE isbn= :isbn",
                      {"isbn": book_isbn}).fetchone()
    if not book:
        return jsonify({"error": "Invalid isbn"}), 422

    review_info = db.execute(
        "SELECT * from reviews WHERE isbn=:isbn", {"isbn": book_isbn}).rowcount

    average_info = db.execute("SELECT AVG(round(rating)) FROM reviews WHERE isbn = :isbn", {
        "isbn": book_isbn}).fetchone()

    average_info = average_info[0]
    if average_info == None:
        average_info = "0"
    return jsonify({
        "title": book['title'],
        "author": book['autor'],
        "year": book['publication_year'],
        "isbn": book['isbn'],
        "review_count": int(review_info),
        "average_score": int(average_info)})
