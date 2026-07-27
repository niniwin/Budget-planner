from models import db


class Note(db.Model):
    __tablename__='notes'
    id=db.Column(db.Integer,primary_key=True)
    content=db.Column(db.Text)
