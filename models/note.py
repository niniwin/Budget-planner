from models import db


class Note(db.Model):
    __tablename__='notes'
    id=db.Column(db.Integer,primary_key=True)
    content=db.Column(db.Text)
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'))
    user=db.relationship('User',backref='notes')
