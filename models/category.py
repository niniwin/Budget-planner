from models import db

class Category(db.Model):
    __tablename__='category'
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100),nullable=False)
    type=db.Column(db.String(10))