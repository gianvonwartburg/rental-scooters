from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from extensions import db
from models import Scooter, User

provider_bp = Blueprint("provider", __name__, url_prefix="/provider")

ALLOWED_STATUSES = ("available", "maintenance")


def get_current_user() -> User | None:
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not get_current_user():
            flash("Bitte zuerst einloggen.")
            return redirect(url_for("auth.login"))
        return fn(*args, **kwargs)

    return wrapper


def provider_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            flash("Bitte zuerst einloggen.")
            return redirect(url_for("auth.login"))
        if user.role != "provider":
            abort(403)
        return fn(*args, **kwargs)

    return wrapper


def get_owned_scooter_or_404(scooter_id: int, provider_id: int) -> Scooter:
    scooter = db.session.get(Scooter, scooter_id)
    if not scooter or scooter.provider_id != provider_id:
        abort(404)
    return scooter


@provider_bp.get("/scooters")
@login_required
@provider_required
def scooters_list():
    user = get_current_user()
    scooters = (
        Scooter.query.filter_by(provider_id=user.user_id)
        .order_by(Scooter.created_at.desc())
        .all()
    )
    return render_template("provider/scooters_list.html", scooters=scooters)


@provider_bp.get("/scooters/new")
@login_required
@provider_required
def scooters_new():
    return render_template("provider/scooters_form.html", scooter=None, statuses=ALLOWED_STATUSES)


@provider_bp.post("/scooters/new")
@login_required
@provider_required
def scooters_new_post():
    user = get_current_user()

    identifier = (request.form.get("scooter_identifier") or "").strip()
    status = (request.form.get("status") or "").strip()
    battery_raw = request.form.get("battery_percent")

    lat_raw = (request.form.get("latitude") or "").strip()
    lng_raw = (request.form.get("longitude") or "").strip()

    if not identifier:
        flash("Scooter-Identifier ist Pflicht.")
        return redirect(url_for("provider.scooters_new"))

    if status not in ALLOWED_STATUSES:
        flash("Ungültiger Status.")
        return redirect(url_for("provider.scooters_new"))

    try:
        battery = int(battery_raw)
        if battery < 0 or battery > 100:
            raise ValueError()
    except Exception:
        flash("Akku muss eine Zahl von 0 bis 100 sein.")
        return redirect(url_for("provider.scooters_new"))

    if Scooter.query.filter_by(scooter_identifier=identifier).first():
        flash("Dieser Scooter-Identifier existiert bereits.")
        return redirect(url_for("provider.scooters_new"))

    # Optional: Koordinaten validieren (nur wenn gesetzt)
    latitude = lat_raw or None
    longitude = lng_raw or None

    scooter = Scooter(
        provider_id=user.user_id,
        scooter_identifier=identifier,
        status=status,
        battery_percent=battery,
        latitude=latitude,
        longitude=longitude,
    )

    db.session.add(scooter)
    db.session.commit()

    flash("Scooter erstellt.")
    return redirect(url_for("provider.scooters_list"))


@provider_bp.get("/scooters/<int:scooter_id>/edit")
@login_required
@provider_required
def scooters_edit(scooter_id: int):
    user = get_current_user()
    scooter = get_owned_scooter_or_404(scooter_id, user.user_id)
    return render_template("provider/scooters_form.html", scooter=scooter, statuses=ALLOWED_STATUSES)


@provider_bp.post("/scooters/<int:scooter_id>/edit")
@login_required
@provider_required
def scooters_edit_post(scooter_id: int):
    user = get_current_user()
    scooter = get_owned_scooter_or_404(scooter_id, user.user_id)

    status = (request.form.get("status") or "").strip()
    battery_raw = request.form.get("battery_percent")

    lat_raw = (request.form.get("latitude") or "").strip()
    lng_raw = (request.form.get("longitude") or "").strip()

    if status not in ALLOWED_STATUSES:
        flash("Ungültiger Status.")
        return redirect(url_for("provider.scooters_edit", scooter_id=scooter_id))

    try:
        battery = int(battery_raw)
        if battery < 0 or battery > 100:
            raise ValueError()
    except Exception:
        flash("Akku muss eine Zahl von 0 bis 100 sein.")
        return redirect(url_for("provider.scooters_edit", scooter_id=scooter_id))

    scooter.status = status
    scooter.battery_percent = battery
    scooter.latitude = lat_raw or None
    scooter.longitude = lng_raw or None

    db.session.commit()
    flash("Scooter gespeichert.")
    return redirect(url_for("provider.scooters_list"))


@provider_bp.post("/scooters/<int:scooter_id>/delete")
@login_required
@provider_required
def scooters_delete_post(scooter_id: int):
    user = get_current_user()
    scooter = get_owned_scooter_or_404(scooter_id, user.user_id)

    # Optional Business Rule: nicht löschen, wenn aktive Miete existiert
    if any(r.status == "active" for r in scooter.rentals):
        flash("Scooter kann nicht gelöscht werden: aktive Miete vorhanden.")
        return redirect(url_for("provider.scooters_list"))

    db.session.delete(scooter)
    db.session.commit()
    flash("Scooter gelöscht.")
    return redirect(url_for("provider.scooters_list"))