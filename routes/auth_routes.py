from functools import wraps
from email.message import EmailMessage
import smtplib

from authlib.integrations.flask_client import OAuth
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from models import db
from models.user import User


auth_bp = Blueprint("auth", __name__)
oauth = OAuth()


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            flash("Admin access is required.", "danger")
            return redirect(url_for("budget.planner"))
        return view(*args, **kwargs)

    return wrapped


@auth_bp.record_once
def register_oauth(state):
    app = state.app
    oauth.init_app(app)
    if app.config.get("OAUTH_CLIENT_ID") and app.config.get("OAUTH_CLIENT_SECRET"):
        oauth.register(
            name="provider",
            client_id=app.config["OAUTH_CLIENT_ID"],
            client_secret=app.config["OAUTH_CLIENT_SECRET"],
            server_metadata_url=app.config["OAUTH_DISCOVERY_URL"],
            client_kwargs={"scope": app.config["OAUTH_SCOPE"]},
        )


def _admin_emails():
    return current_app.config.get("ADMIN_EMAILS", set())


def _role_for_email(email):
    normalized = (email or "").lower()
    if normalized in _admin_emails() or User.query.count() == 0:
        return "admin"
    return "user"


def _password_reset_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def _password_reset_token(user):
    return _password_reset_serializer().dumps(
        {"user_id": user.id, "password_hash": user.password_hash},
        salt="password-reset",
    )


def _user_from_reset_token(token):
    try:
        data = _password_reset_serializer().loads(token, salt="password-reset", max_age=3600)
    except (BadSignature, SignatureExpired):
        return None

    user = db.session.get(User, data.get("user_id"))
    if not user or user.password_hash != data.get("password_hash"):
        return None
    return user


def _send_password_reset_email(user):
    config = current_app.config
    required_settings = ("MAIL_SERVER", "MAIL_USERNAME", "MAIL_PASSWORD", "MAIL_DEFAULT_SENDER")
    if not all(config.get(setting) for setting in required_settings):
        current_app.logger.warning("Password-reset email was requested but mail is not configured.")
        return False

    reset_url = url_for("auth.reset_password", token=_password_reset_token(user), _external=True)
    message = EmailMessage()
    message["Subject"] = "Reset your Budget Planner password"
    message["From"] = config["MAIL_DEFAULT_SENDER"]
    message["To"] = user.email
    message.set_content(
        "A password reset was requested for your Budget Planner account.\n\n"
        f"Reset your password: {reset_url}\n\n"
        "This link expires in one hour. If you did not request it, you can ignore this email."
    )

    with smtplib.SMTP(config["MAIL_SERVER"], config["MAIL_PORT"]) as server:
        if config["MAIL_USE_TLS"]:
            server.starttls()
        server.login(config["MAIL_USERNAME"], config["MAIL_PASSWORD"])
        server.send_message(message)
    return True


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("budget.planner"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("Username, email, and password are required.", "danger")
            return render_template("auth/register.html")

        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("That username or email is already registered.", "danger")
            return render_template("auth/register.html")

        user = User(username=username, email=email, role=_role_for_email(email))
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Your account is ready. Please sign in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("budget.planner"))

    if request.method == "POST":
        identity = request.form.get("identity", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter((User.username == identity) | (User.email == identity.lower())).first()

        if user and user.check_password(password):
            login_user(user, remember=bool(request.form.get("remember")))
            flash("Welcome back.", "success")
            next_url = request.args.get("next")
            return redirect(next_url or url_for("budget.planner"))

        flash("Invalid username/email or password.", "danger")

    oauth_enabled = hasattr(oauth, "provider")
    return render_template(
        "auth/login.html",
        oauth_enabled=oauth_enabled,
        oauth_provider_name=current_app.config.get("OAUTH_PROVIDER_NAME", "OAuth"),
    )


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("budget.planner"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user and user.email:
            try:
                _send_password_reset_email(user)
            except (OSError, smtplib.SMTPException):
                current_app.logger.exception("Could not send password-reset email.")

        # Keep this message identical whether or not an account exists.
        flash("If that email belongs to an account, a reset link has been sent.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("budget.planner"))

    user = _user_from_reset_token(token)
    if not user:
        flash("This password-reset link is invalid or has expired.", "danger")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        if len(password) < 8:
            flash("Use a password with at least 8 characters.", "danger")
        elif password != confirm_password:
            flash("The passwords do not match.", "danger")
        else:
            user.set_password(password)
            db.session.commit()
            flash("Your password has been reset. Please sign in.", "success")
            return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html")


@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not current_user.check_password(current_password):
            flash("Your current password is incorrect.", "danger")
        elif len(password) < 8:
            flash("Use a password with at least 8 characters.", "danger")
        elif password != confirm_password:
            flash("The passwords do not match.", "danger")
        else:
            current_user.set_password(password)
            db.session.commit()
            flash("Your password has been changed.", "success")
            return redirect(url_for("budget.planner"))

    return render_template("auth/change_password.html")


@auth_bp.route("/login/oauth")
def oauth_login():
    if not hasattr(oauth, "provider"):
        flash("OAuth is not configured yet.", "warning")
        return redirect(url_for("auth.login"))

    redirect_uri = url_for("auth.oauth_callback", _external=True)
    return oauth.provider.authorize_redirect(redirect_uri)


@auth_bp.route("/auth/callback")
def oauth_callback():
    if not hasattr(oauth, "provider"):
        flash("OAuth is not configured yet.", "warning")
        return redirect(url_for("auth.login"))

    token = oauth.provider.authorize_access_token()
    userinfo = token.get("userinfo") or oauth.provider.userinfo(token=token)
    email = (userinfo.get("email") or "").lower()
    subject = userinfo.get("sub")

    if not email or not subject:
        flash("The OAuth provider did not return an email address.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(oauth_provider="provider", oauth_subject=subject).first()
    if not user:
        user = User.query.filter_by(email=email).first()

    if not user:
        username = email.split("@")[0]
        base_username = username
        suffix = 1
        while User.query.filter_by(username=username).first():
            suffix += 1
            username = f"{base_username}{suffix}"

        user = User(
            username=username,
            email=email,
            role=_role_for_email(email),
            oauth_provider="provider",
            oauth_subject=subject,
        )
        db.session.add(user)
    else:
        user.oauth_provider = "provider"
        user.oauth_subject = subject
        if email in _admin_emails():
            user.role = "admin"

    db.session.commit()
    login_user(user)
    flash("Signed in with OAuth.", "success")
    return redirect(url_for("budget.planner"))


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/admin/users", methods=["GET", "POST"])
@admin_required
def admin_users():
    if request.method == "POST":
        user = User.query.get_or_404(request.form.get("user_id"))
        role = request.form.get("role")
        if role not in {"user", "admin"}:
            flash("Invalid role.", "danger")
        elif user.id == current_user.id and role != "admin":
            flash("You cannot remove your own admin role.", "warning")
        else:
            user.role = role
            db.session.commit()
            flash(f"{user.username} is now {role}.", "success")

        return redirect(url_for("auth.admin_users"))

    users = User.query.order_by(User.id.asc()).all()
    return render_template("auth/admin_users.html", users=users)
