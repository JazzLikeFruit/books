import os

from flask import Flask, session, render_template, request, flash, url_for, redirect
from flask_session import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


# Log in page
@app.route("/", methods=['GET', 'POST'])
def index():
    error = ''

    if request.method == 'POST':
        attempted_username = request.form['username'].strip()
        attempted_password = request.form['password']

        if db.execute("SELECT * FROM users WHERE username = :username AND password = :password",
                      {"username": attempted_username, "password": attempted_password}).rowcount == 0:
            error = "invalid username/password. Try again."
            return render_template("index.html", error=error)
        return redirect(url_for('homepage'))

    return render_template("index.html")


# Registration page
@app.route("/registration/", methods=["GET", "POST"])
def registration():
    error = ''
    if request.method == 'POST':
        username = request.form["username"]
        password = request.form["password"]

        if db.execute("SELECT * FROM users WHERE username = :user", {
                "user": username
        }).rowcount == 0:
            db.execute(
                "INSERT INTO users (username, password) VALUES (:name, :pass)", {
                    "name": username,
                    "pass": password
                })
            db.commit()
            error = "Succes! Please log in."
            return render_template("registration.html", error=error)

        else:
            error = "Username already in use."
            return render_template("registration.html", error=error)

    return render_template("registration.html")


# Home page
@app.route("/homepage/")
def homepage():
    books = db.execute("SELECT * FROM books").fetchall()
    return render_template("homepage.html", books=books)


# Book page
@app.route("/search/<string:book_isbn>")
def book(book_isbn):
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {
        "isbn": book_isbn
    }).fetchone()
    if book is None:
        return render_template("error.html", message="Book not found")
    return render_template("book.html", book=book)


# Seach result page
@app.route("/search", methods=["POST"])
def search():
    name = request.form.get("name").title()
    results = db.execute(
        "select * from books where autor LIKE :name or title LIKE :name or isbn LIKE :name",
        {"name": "%" + name + "%"})
    if results.rowcount == 0:
        return render_template("error.html", message="No results")
    return render_template("search.html", results=results)
