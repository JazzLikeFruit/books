import os
import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(
    "postgres://jxsmvxqneenqco:08e745af9ab4848178f9f4fa3c86ac6ae6aa7c8b7fde1c24b76b3424f9fd968d@ec2-54-228-251-117.eu-west-1.compute.amazonaws.com:5432/d11vpr3alp1a5p"
)  # database engine object from SQLAlchemy that manages connections to the database
# DATABASE_URL is an environment variable that indicates where the database lives
db = scoped_session(
    sessionmaker(bind=engine)
)  # create a 'scoped session' that ensures different users' interactions with the
# database are kept separate

file = open("books.csv")
reader = csv.reader(file)
next(reader)
for isbn, title, autor, publication_year in reader:  # loop gives each column a name

    db.execute(
        "INSERT INTO books (isbn, title, autor, publication_year) VALUES (:isbn, :title, :autor, :publication_year)",
        {"isbn": isbn, "title": title, "autor": autor,
            "publication_year": publication_year}
    )  # substitute values from CSV line into SQL command, as per this dict
    print(
        f"Added book {isbn} titled {title} writen by {autor} in the year {publication_year}."
    )
db.commit()  # transactions are assumed, so close the transaction finished
