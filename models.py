from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class books (db.Model):
    __tablename__ = "books"
    isbn = db.Column (db.String, primary_key=True)
    autor = db.Column (db.String, nullable=False)
    publication_year = (db.Column, nullable=False)
    title = db.Column (db.String, nullable=False)

class reviews (db.Model):
    __tablename__ = "reviews"
    username = db.Column (db.String, primary_key=True, db.ForeignKey("users.username")) 
    isbn = db.Column (db.String, primary_key=True, db.ForeignKey("books.isbn"))
    text = db.Column (db.String, nullable=False)
    rating = db.Column (db.Integer, nullable=False)


class users (db.Model):
    __tablename__ = "users"
    username = db.Column (db.String, primary_key=True)
    password = db.Column (db.String, nullable=False)
    