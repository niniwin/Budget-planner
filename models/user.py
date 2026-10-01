from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from models import db 


class User(UserMixin, db.Model):
    __tablename__='user'

    id=db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(100),unique=True,nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(20), nullable=False, default="user")
    oauth_provider = db.Column(db.String(50), nullable=True)
    oauth_subject = db.Column(db.String(255), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "admin"
