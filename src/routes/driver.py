from functools import wraps
from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from extensions import db
from models import Rental, Scooter, User

from datetime import datetime
from decimal import Decimal

driver_bp = Blueprint("driver", __name__, url_prefix="/driver")


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


def driver_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            flash("Bitte zuerst einloggen.")
            return redirect(url_for("auth.login"))
        if user.role != "driver":
            abort(403)
        return fn(*args, **kwargs)

    return wrapper


def get_active_rental_for_driver(driver_id: int) -> Rental | None:
    return Rental.query.filter_by(driver_id=driver_id, status="active").first()


@driver_bp.get("/scooters")
@login_required
@driver_required
def scooters_list():
    user = get_current_user()

    active_rental = get_active_rental_for_driver(user.user_id)
    if active_rental:
        # Optional: Wenn schon aktiv gemietet, direkt anzeigen
        return render_template("driver/rental_active.html", rental=active_rental)

    scooters = Scooter.query.filter_by(status="available").order_by(Scooter.created_at.desc()).all()
    return render_template("driver/scooters_list.html", scooters=scooters)


@driver_bp.post("/rent/<int:scooter_id>")
@login_required
@driver_required
def start_rental(scooter_id: int):
    user = get_current_user()

    # Business rule: ein Driver darf nur 1 aktive Miete haben
    if get_active_rental_for_driver(user.user_id):
        flash("Du hast bereits eine aktive Miete.")
        return redirect(url_for("driver.scooters_list"))

    scooter = db.session.get(Scooter, scooter_id)
    if not scooter or scooter.status != "available":
        flash("Scooter ist nicht verfügbar.")
        return redirect(url_for("driver.scooters_list"))

    # Statuswechsel + Rental anlegen
    scooter.status = "rented"
    rental = Rental(
        scooter_id=scooter.scooter_id,
        driver_id=user.user_id,
        status="active",
    )

    db.session.add(rental)
    db.session.commit()

    flash("Miete gestartet.")
    return redirect(url_for("driver.scooters_list"))


@driver_bp.get("/rent/<int:rental_id>/finish")
@login_required
@driver_required
def finish_rental_form(rental_id: int):
    user = get_current_user()

    rental = db.session.get(Rental, rental_id)
    if not rental or rental.driver_id != user.user_id:
        abort(404)

    if rental.status != "active":
        flash("Miete ist nicht aktiv.")
        return redirect(url_for("driver.scooters_list"))

    scooter = db.session.get(Scooter, rental.scooter_id)
    return render_template("driver/rental_finish.html", rental=rental, scooter=scooter)

@driver_bp.post("/rent/<int:rental_id>/finish")
@login_required
@driver_required
def finish_rental(rental_id: int):
    user = get_current_user()

    rental = db.session.get(Rental, rental_id)
    if not rental or rental.driver_id != user.user_id:
        abort(404)

    if rental.status != "active":
        flash("Miete ist nicht aktiv.")
        return redirect(url_for("driver.scooters_list"))

    battery_raw = request.form.get("battery_percent")
    distance_raw = (request.form.get("distance_km") or "").strip()
    lat_raw = (request.form.get("latitude") or "").strip()
    lng_raw = (request.form.get("longitude") or "").strip()

    # Battery required
    try:
        battery = int(battery_raw)
        if battery < 0 or battery > 100:
            raise ValueError()
    except Exception:
        flash("Akku muss eine Zahl von 0 bis 100 sein.")
        return redirect(url_for("driver.finish_rental_form", rental_id=rental_id))

    # Distance optional
    distance = None
    if distance_raw:
        try:
            distance = Decimal(distance_raw)
            if distance < 0:
                raise ValueError()
        except Exception:
            flash("Distanz muss eine positive Zahl sein.")
            return redirect(url_for("driver.finish_rental_form", rental_id=rental_id))

    scooter = db.session.get(Scooter, rental.scooter_id)
    if not scooter:
        flash("Scooter nicht gefunden.")
        return redirect(url_for("driver.scooters_list"))

    # Apply updates
    scooter.battery_percent = battery
    scooter.latitude = lat_raw or None
    scooter.longitude = lng_raw or None
    scooter.status = "available"

    rental.distance_km = distance
    rental.status = "finished"
    rental.end_time = datetime.utcnow()

    db.session.commit()

    flash("Miete beendet.")
    return redirect(url_for("driver.scooters_list"))
