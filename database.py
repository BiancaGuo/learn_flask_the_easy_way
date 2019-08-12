from flask_sqlalchemy import SQLAlchemy
from flask import Flask
db = SQLAlchemy()


def connect_database():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:700516@localhost:3306/watermark'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    return app


