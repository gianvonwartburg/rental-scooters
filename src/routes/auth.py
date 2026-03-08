from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db
from models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.get("/register")
def register():
    return render_template("register.html")


@auth_bp.post("/register")
def register_post():
    username = (request.form.get("username") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    role = request.form.get("role") or ""

    if role not in ("provider", "driver"):
        flash("Ungültige Rolle.", "danger")
        return redirect(url_for("auth.register"))

    if not username or not email or not password:
        flash("Bitte alle Felder ausfüllen.", "warning")
        return redirect(url_for("auth.register"))

    if User.query.filter_by(username=username).first():
        flash("Username ist bereits vergeben.", "warning")
        return redirect(url_for("auth.register"))

    if User.query.filter_by(email=email).first():
        flash("E-Mail ist bereits vergeben.", "warning")
        return redirect(url_for("auth.register"))

    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        role=role,
    )
    db.session.add(user)
    db.session.commit()

    flash("Registrierung erfolgreich. Bitte einloggen.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.get("/login")
def login():
    return render_template("login.html")


@auth_bp.post("/login")
def login_post():
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        flash("Login fehlgeschlagen.", "danger")
        return redirect(url_for("auth.login"))

    session["user_id"] = user.user_id
    flash("Erfolgreich eingeloggt.", "success")
    return redirect(url_for("home"))


@auth_bp.get("/logout")
def logout():
    session.pop("user_id", None)
    flash("Ausgeloggt.", "info")
    return redirect(url_for("home"))
