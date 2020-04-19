import os
import csv
from models import *

from flask import Flask, render_template, request

app = Flask(__name__)

# Tell Flask what SQLAlchemy databas to use.
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Link the Flask app with the database (no Flask app is actually being run yet).
db.init_app(app)


def main():
    db.create_all()
    
    file = open("books.csv")
    reader = csv.reader(file)
    next(reader)
    for isbn, title, autor, publication_year in reader:  # loop gives each column a name
        book = Books(isbn=isbn, title=title, autor=autor,
                     publication_year=publication_year)
        db.session.add(book)
        print(
            f"Added book {isbn} titled {title} writen by {autor} in the year {publication_year}."
        )
        db.session.flush()
    db.session.commit()


if __name__ == "__main__":
    # Allows for command line interaction with Flask application
    with app.app_context():
        main()
