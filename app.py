from flask import Flask, redirect,render_template,url_for, request, session, flash
import datetime 
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from models import db
from config import Config
from routes.budget_routes import budget_bp

app=Flask(__name__)
app.secret_key="jello"
app.permanent_session_lifetime=timedelta(minutes=5)
app.config.from_object(Config)
app.register_blueprint(budget_bp)

db.init_app(app)

# import models so SQLAlchemy knows them
from models.user import User
from models.category import Category
from models.transaction import Transaction


with app.app_context():
    db.create_all()

@app.route("/")
def budget():
    month=datetime.datetime.now().strftime("%B")
    return render_template("budget.html",month=month)

if __name__=="__main__":
    app.run()


with app.app_context():
    db.drop_all()
    db.create_all()