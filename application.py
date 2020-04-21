import os

from flask import Flask, session, render_template, request, url_for, redirect
from flask_sqlalchemy import sqlalchemy
from flask_paginate import Pagination
from models import *
from sqlalchemy import and_, or_

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Log in page
@app.route("/", methods=['GET', 'POST'])
def index():
    error = ''

    if request.method == 'POST':
        attempted_username = request.form['username']
        attempted_password = request.form['password']
        if Users.query.filter(
                and_(Users.username == attempted_username, Users.password == attempted_password)).count() == 0:
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

        if Users.query.get(username) is None:
            user = Users(username=username, password=password)
            db.session.add(user)
            db.session.commit()
            error = "Your username has been added! Please log in."
            return render_template("registration.html", error=error)

        else:
            error = "Username already in use."
            return render_template("registration.html", error=error)

    return render_template("registration.html")


# Home page
@app.route("/homepage/<int:page_num>")
def homepage(page_num):
    books = Books.query.paginate(per_page=100, page=page_num, error_out=True)
    return render_template("homepage.html", books=books)


# Book page
@app.route("/search/<string:book_isbn>")
def book(book_isbn):
    book = Books.query.get(book_isbn)
    if book is None:
        return render_template("error.html", message="Book not found")
    return render_template("book.html", book=book)


# Seach result page
@app.route("/search", methods=["POST"])
def search():
    name = "%{}%".format(request.form.get("name").title())
    results = Books.query.filter(
        or_(Books.autor.like(name), Books.title.like(name), Books.isbn.like(name))).all()
    if Books.query.filter(
            or_(Books.autor.like(name), Books.title.like(name), Books.isbn.like(name))).count() is 0:
        return render_template("error.html", message="No results")
    return render_template("search.html", results=results)
