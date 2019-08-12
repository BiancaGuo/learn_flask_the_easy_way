from database import db
from flask_login import UserMixin#用户会话管理


class Users(db.Model,UserMixin):
    __tablename__ = 'users'
    # id是主键db.Column是字段名， db.INT是数据类型
    id = db.Column(db.INT, primary_key=True)
    email = db.Column(db.VARCHAR(500),unique=True)
    password = db.Column(db.VARCHAR(500),unique=True)

    def __init__(self, id, email, password):
        self.id = id
        self.email = email
        self.password = password

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id
    def __repr__(self):
        return '<User %r>' % self.email
