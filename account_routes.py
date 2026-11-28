"""Account pages, session authentication, and account APIs."""
import os
import re
import secrets
from datetime import timedelta
from functools import wraps
from urllib.parse import urlsplit

import mysql.connector
from flask import Blueprint, abort, g, jsonify, make_response, redirect, request, session, url_for
from markupsafe import escape
from werkzeug.security import check_password_hash, generate_password_hash

import account_db as db
from accounts_pages import DASHBOARD, HISTORY, LOGIN, REGISTER, render_page

pages = Blueprint("account_pages", __name__, url_prefix="/account")
api = Blueprint("account_api", __name__, url_prefix="/api/account")


def _current_user():
    return getattr(g, "account_user", None)


def _screen(title, contents, **context):
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return render_page(title, contents, user=_current_user(), csrf_token=session["csrf_token"], **context)


@pages.before_request
def _check_csrf():
    if request.method == "POST":
        expected = session.get("csrf_token", "")
        supplied = request.form.get("csrf_token", "")
        if not expected or not secrets.compare_digest(expected, supplied):
            abort(400, description="Invalid form token. Reload the page and try again.")


def _needs_login(handler):
    @wraps(handler)
    def wrapped(*args, **kwargs):
        if _current_user() is None:
            return redirect(url_for("account_pages.login", next=request.path))
        return handler(*args, **kwargs)
    return wrapped


def _safe_next(value):
    parts = urlsplit(value)
    if value.startswith("/") and not value.startswith("//") and not parts.netloc and not parts.scheme and "\\" not in value:
        return value
    return url_for("account_pages.dashboard")


def _serialize_user(user):
    return {key: user[key] for key in ("user_id", "username", "email")}


def _serialize_history(records):
    return [{**record, "created_at": str(record["created_at"])} for record in records]


def _profile_error(username, email):
    if not re.fullmatch(r"[A-Za-z0-9_]{3,32}", username):
        return "Username must contain 3–32 letters, numbers, or underscores."
    if len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        return "Enter a valid email address."


def _password_error(password, confirm):
    if not 12 <= len(password) <= 128:
        return "Password must contain 12–128 characters."
    if password != confirm:
        return "Passwords do not match."


def _sign_in(user):
    session.clear()
    session.permanent = True
    session["account_user_id"] = user["user_id"]
    session["account_session_version"] = user["session_version"]


@pages.route("/login", methods=["GET", "POST"])
def login():
    next_path = _safe_next(request.values.get("next", ""))
    login_value = request.form.get("login", "").strip()
    error = None
    if request.method == "POST":
        user = db.find_user_by_login(login_value)
        password = request.form.get("password", "")
        if user and len(password) <= 128 and check_password_hash(user["password_hash"], password):
            _sign_in(user)
            return redirect(next_path, code=303)
        error = "Username/email or password is incorrect."
    return _screen("Log in", LOGIN, error=error, next_path=next_path, login_value=login_value), 400 if error else 200


@pages.route("/register", methods=["GET", "POST"])
def register():
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip().lower()
    error = None
    if request.method == "POST":
        password = request.form.get("password", "")
        error = _profile_error(username, email) or _password_error(password, request.form.get("confirm", ""))
        if not error:
            try:
                user_id = db.create_user(username, email, generate_password_hash(password))
            except mysql.connector.IntegrityError as exc:
                if exc.errno != 1062:
                    raise
                error = "That username or email is already in use."
            else:
                _sign_in(db.find_user_by_id(user_id))
                return redirect(url_for("account_pages.dashboard"), code=303)
    return _screen("Sign up", REGISTER, error=error, username_value=username, email_value=email), 400 if error else 200


@pages.get("")
@_needs_login
def dashboard():
    return _screen("My account", DASHBOARD)


@pages.post("/profile")
@_needs_login
def profile():
    user = _current_user()
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip().lower()
    error = _profile_error(username, email)
    if not check_password_hash(user["password_hash"], request.form.get("current_password", "")):
        error = "Current password is incorrect."
    if not error:
        try:
            db.update_profile(user["user_id"], username, email)
        except mysql.connector.IntegrityError as exc:
            if exc.errno != 1062:
                raise
            error = "That username or email is already in use."
    if error:
        return _screen("My account", DASHBOARD, error=error), 400
    return redirect(url_for("account_pages.dashboard"), code=303)


@pages.post("/password")
@_needs_login
def password():
    user = _current_user()
    new_password = request.form.get("new_password", "")
    error = _password_error(new_password, request.form.get("confirm", ""))
    if not check_password_hash(user["password_hash"], request.form.get("current_password", "")):
        error = "Current password is incorrect."
    if error:
        return _screen("My account", DASHBOARD, error=error), 400
    session["account_session_version"] = db.change_password(user["user_id"], generate_password_hash(new_password))
    return redirect(url_for("account_pages.dashboard"), code=303)


@pages.post("/logout")
@_needs_login
def logout():
    session.clear()
    return redirect(url_for("home"), code=303)


@pages.post("/delete")
@_needs_login
def delete():
    user = _current_user()
    if request.form.get("confirmation") != "DELETE":
        return _screen("My account", DASHBOARD, error="Type DELETE to confirm account deletion."), 400
    if not check_password_hash(user["password_hash"], request.form.get("current_password", "")):
        return _screen("My account", DASHBOARD, error="Current password is incorrect."), 400
    db.delete_user(user["user_id"])
    session.clear()
    return redirect(url_for("home"), code=303)


@pages.get("/history")
@_needs_login
def history():
    records = db.submission_history(_current_user()["user_id"])
    return _screen("My votes", HISTORY, submissions=records)


@api.get("/me")
def get_current_account():
    user = _current_user()
    if user is None:
        return jsonify({"error": "Authentication required"}), 401
    return jsonify(_serialize_user(user))


@api.get("/submissions")
def get_account_submissions():
    user = _current_user()
    if user is None:
        return jsonify({"error": "Authentication required"}), 401
    return jsonify({"submissions": _serialize_history(db.submission_history(user["user_id"]))})


def register_account_features(app):
    """Register account endpoints and enhancements on the existing Flask app.

    Must be called once, before serving requests, after importing ProjectBe.
    """
    if not os.getenv("ACCOUNT_SECRET_KEY"):
        raise RuntimeError(
            "Set ACCOUNT_SECRET_KEY in .env to a randomly generated secret. "
            "Example: python -c 'import secrets; print(secrets.token_hex(32))'"
        )
    if len(os.environ["ACCOUNT_SECRET_KEY"]) < 32:
        raise RuntimeError("ACCOUNT_SECRET_KEY must be at least 32 characters.")

    app.config.update(
        SECRET_KEY=os.environ["ACCOUNT_SECRET_KEY"],
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("ACCOUNT_COOKIE_SECURE", "0") == "1",
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
    )

    @app.before_request
    def load_account_user():
        g.account_user = None
        user_id = session.get("account_user_id")
        version = session.get("account_session_version")
        if type(user_id) is not int or type(version) is not int:
            if user_id is not None:
                session.clear()
            return
        user = db.find_user_by_id(user_id)
        if not user or user["session_version"] != version:
            session.clear()
            return
        g.account_user = user

    app.register_blueprint(pages)
    app.register_blueprint(api)

    # Original ProjectBe.add_response() includes the newly inserted submission_id
    # in its success JSON. Decorate it at runtime, without modifying ProjectBe.py.
    existing_handler = app.view_functions["add_response"]

    @wraps(existing_handler)
    def record_account_ownership():
        response = make_response(existing_handler())
        user = _current_user()
        if response.status_code == 201 and user is not None:
            data = response.get_json(silent=True)
            submission_id = data.get("submission_id") if isinstance(data, dict) else None
            if type(submission_id) is int and submission_id > 0:
                try:
                    db.link_submission(user["user_id"], submission_id)
                except mysql.connector.Error:
                    # Survey was already committed by the original endpoint.
                    # Do not claim an account association that failed.
                    app.logger.exception("Could not associate submission with account")
                    data["account_history_saved"] = False
                    data["warning"] = "Vote was recorded but could not be linked to your account."
                    response.set_data(app.json.dumps(data))
                else:
                    data["account_history_saved"] = True
                    response.set_data(app.json.dumps(data))
        return response

    app.view_functions["add_response"] = record_account_ownership

    @app.after_request
    def append_account_links(response):
        # Both existing templates have a header <nav>...</nav>. Insert links
        # in the outgoing HTML only, keeping their source files unchanged.
        if request.path not in ("/", "/results") or response.status_code != 200:
            return response
        if response.mimetype != "text/html" or response.direct_passthrough:
            return response
        body = response.get_data(as_text=True)
        if "</nav>" not in body:
            return response
        user = _current_user()
        if user:
            nickname = escape(user["username"])
            nav = (f'<a href="/account">{nickname} · Account</a> '
                   '<a href="/account/history">My votes</a>')
        else:
            nav = ('<a href="/account/login">Log in</a> '
                   '<a href="/account/register">Sign up</a>')
        response.set_data(body.replace("</nav>", nav + "</nav>", 1))
        return response
