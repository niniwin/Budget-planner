from datetime import timedelta

from flask import Flask
from flask_login import LoginManager

from config import Config
from models import db
from routes.auth_routes import auth_bp
from routes.budget_routes import budget_bp
from routes.report_routes import report_bp

app = Flask(__name__)
app.config.from_object(Config)

app.permanent_session_lifetime = timedelta(minutes=5)

db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"
login_manager.init_app(app)

app.register_blueprint(budget_bp)
app.register_blueprint(report_bp)
app.register_blueprint(auth_bp)

# Import models so SQLAlchemy registers them.
from models.category import Category
from models.note import Note
from models.transaction import Transaction
from models.user import User


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


if app.config["AUTO_CREATE_TABLES"]:
    with app.app_context():
        db.create_all()


if __name__ == "__main__":
    app.run(debug=False)
