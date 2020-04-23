from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Books (db.Model):
    __tablename__ = "books"
    isbn = db.Column(db.String, primary_key=True)
    autor = db.Column(db.String, nullable=False)
    publication_year = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String, nullable=False)


class Reviews (db.Model):
    __tablename__ = "reviews"
    username = db.Column(db.String, db.ForeignKey(
        "users.username"), primary_key=True)
    isbn = db.Column(db.String, db.ForeignKey("books.isbn"), primary_key=True)
    text = db.Column(db.String, nullable=False)
    rating = db.Column(db.Integer, nullable=False)


class Users (db.Model):
    __tablename__ = "users"
    username = db.Column(db.String, primary_key=True)
    password = db.Column(db.String, nullable=False)
