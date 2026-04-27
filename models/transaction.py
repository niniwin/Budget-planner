
from models import db
from sqlalchemy import func
from sqlalchemy import Enum

class Transaction(db.Model):
    __tablename__='transactions'

    id=db.Column(db.Integer,primary_key=True)
    amount = db.Column(db.Float,nullable=False)
    description= db.Column(db.Text)
    date=db.Column(db.Date, default=func.now())
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'))
    category_id=db.Column(db.Integer,db.ForeignKey('category.id'))
    user=db.relationship('User',backref='transactions')
    category=db.relationship('Category',backref='transactions')
    type = db.Column(Enum('income', 'expense', name='transaction_type'), nullable=False)