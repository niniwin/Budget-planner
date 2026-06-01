from flask import Flask
from datetime import timedelta

from config import Config
from models import db
from routes.budget_routes import budget_bp

app = Flask(__name__)
app.config.from_object(Config)

app.permanent_session_lifetime = timedelta(minutes=5)

db.init_app(app)
app.register_blueprint(budget_bp)

# Import models so SQLAlchemy registers them
from models.user import User
from models.category import Category
from models.transaction import Transaction

with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=False)
