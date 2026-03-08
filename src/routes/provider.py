from functools import wraps
from decimal import Decimal, InvalidOperation

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for
from sqlalchemy import and_, func

from extensions import db
from models import Rental, Scooter, User

provider_bp = Blueprint("provider", __name__, url_prefix="/provider")

ALLOWED_STATUSES = ("available", "maintenance")


def get_current_user() -> User | None:
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


def provider_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            flash("Bitte zuerst einloggen.", "warning")
            return redirect(url_for("auth.login"))
        if user.role != "provider":
            abort(403)
        return fn(*args, **kwargs)

    return wrapper


def parse_decimal_or_none(value: str | None, min_value: Decimal | None = None, max_value: Decimal | None = None) -> Decimal | None:
    raw = (value or "").strip()
    if not raw:
        return None

    normalized = raw.replace(",", ".")
    try:
        parsed = Decimal(normalized)
    except InvalidOperation as exc:
        raise ValueError("not_a_number") from exc

    if min_value is not None and parsed < min_value:
        raise ValueError("out_of_range")
    if max_value is not None and parsed > max_value:
        raise ValueError("out_of_range")
    return parsed


def get_owned_scooter_or_404(scooter_id: int, provider_id: int) -> Scooter:
    scooter = db.session.get(Scooter, scooter_id)
    if not scooter or scooter.provider_id != provider_id:
        abort(404)
    return scooter


@provider_bp.get("/scooters")
@provider_required
def scooters_list():
    user = get_current_user()
    scooters = (
        Scooter.query.filter_by(provider_id=user.user_id)
        .order_by(Scooter.created_at.desc())
        .all()
    )
    return render_template("provider/scooters_list.html", scooters=scooters)


@provider_bp.get("/earnings")
@provider_required
def earnings():
    user = get_current_user()
    finished_rental_join = and_(
        Rental.scooter_id == Scooter.scooter_id,
        Rental.status == "finished",
        Rental.price_total.isnot(None),
    )
    revenue_total_expr = func.coalesce(func.sum(Rental.price_total), 0)

    rows = (
        db.session.query(
            Scooter.scooter_identifier.label("scooter_identifier"),
            func.count(Rental.rental_id).label("rentals_count"),
            func.coalesce(func.sum(Rental.billed_minutes), 0).label("minutes_total"),
            revenue_total_expr.label("revenue_total"),
        )
        .outerjoin(Rental, finished_rental_join)
        .filter(Scooter.provider_id == user.user_id)
        .group_by(Scooter.scooter_id, Scooter.scooter_identifier)
        .order_by(revenue_total_expr.desc(), Scooter.scooter_identifier.asc())
        .all()
    )

    totals = {
        "rentals_count": sum(int(row.rentals_count or 0) for row in rows),
        "minutes_total": sum(int(row.minutes_total or 0) for row in rows),
        "revenue_total": sum(
            (Decimal(str(row.revenue_total or 0)) for row in rows),
            Decimal("0.00"),
        ),
    }

    return render_template("provider/earnings.html", rows=rows, totals=totals)


@provider_bp.get("/scooters/new")
@provider_required
def scooters_new():
    return render_template("provider/scooters_form.html", scooter=None, statuses=ALLOWED_STATUSES)


@provider_bp.post("/scooters/new")
@provider_required
def scooters_new_post():
    user = get_current_user()

    identifier = (request.form.get("scooter_identifier") or "").strip()
    status = (request.form.get("status") or "").strip()
    battery_raw = request.form.get("battery_percent")

    lat_raw = (request.form.get("latitude") or "").strip()
    lng_raw = (request.form.get("longitude") or "").strip()

    if not identifier:
        flash("Scooter-Identifier ist Pflicht.", "warning")
        return redirect(url_for("provider.scooters_new"))

    if status not in ALLOWED_STATUSES:
        flash("Ungültiger Status.", "warning")
        return redirect(url_for("provider.scooters_new"))

    try:
        battery = int(battery_raw)
        if battery < 0 or battery > 100:
            raise ValueError()
    except Exception:
        flash("Akku muss eine Zahl von 0 bis 100 sein.", "warning")
        return redirect(url_for("provider.scooters_new"))

    if Scooter.query.filter_by(scooter_identifier=identifier).first():
        flash("Dieser Scooter-Identifier existiert bereits.", "warning")
        return redirect(url_for("provider.scooters_new"))

    try:
        latitude = parse_decimal_or_none(lat_raw, Decimal("-90"), Decimal("90"))
        longitude = parse_decimal_or_none(lng_raw, Decimal("-180"), Decimal("180"))
    except ValueError as exc:
        if str(exc) == "not_a_number":
            flash("Koordinaten müssen Zahlen sein.", "warning")
        else:
            flash("Koordinaten außerhalb des gültigen Bereichs.", "warning")
        return redirect(url_for("provider.scooters_new"))

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

    flash("Scooter erstellt.", "success")
    return redirect(url_for("provider.scooters_list"))


@provider_bp.get("/scooters/<int:scooter_id>/edit")
@provider_required
def scooters_edit(scooter_id: int):
    user = get_current_user()
    scooter = get_owned_scooter_or_404(scooter_id, user.user_id)
    return render_template("provider/scooters_form.html", scooter=scooter, statuses=ALLOWED_STATUSES)


@provider_bp.post("/scooters/<int:scooter_id>/edit")
@provider_required
def scooters_edit_post(scooter_id: int):
    user = get_current_user()
    scooter = get_owned_scooter_or_404(scooter_id, user.user_id)

    status = (request.form.get("status") or "").strip()
    battery_raw = request.form.get("battery_percent")

    lat_raw = (request.form.get("latitude") or "").strip()
    lng_raw = (request.form.get("longitude") or "").strip()

    if status not in ALLOWED_STATUSES:
        flash("Ungültiger Status.", "warning")
        return redirect(url_for("provider.scooters_edit", scooter_id=scooter_id))

    try:
        battery = int(battery_raw)
        if battery < 0 or battery > 100:
            raise ValueError()
    except Exception:
        flash("Akku muss eine Zahl von 0 bis 100 sein.", "warning")
        return redirect(url_for("provider.scooters_edit", scooter_id=scooter_id))

    scooter.status = status
    scooter.battery_percent = battery
    try:
        scooter.latitude = parse_decimal_or_none(lat_raw, Decimal("-90"), Decimal("90"))
        scooter.longitude = parse_decimal_or_none(lng_raw, Decimal("-180"), Decimal("180"))
    except ValueError as exc:
        if str(exc) == "not_a_number":
            flash("Koordinaten müssen Zahlen sein.", "warning")
        else:
            flash("Koordinaten außerhalb des gültigen Bereichs.", "warning")
        return redirect(url_for("provider.scooters_edit", scooter_id=scooter_id))

    db.session.commit()
    flash("Scooter gespeichert.", "success")
    return redirect(url_for("provider.scooters_list"))


@provider_bp.post("/scooters/<int:scooter_id>/delete")
@provider_required
def scooters_delete_post(scooter_id: int):
    user = get_current_user()
    scooter = get_owned_scooter_or_404(scooter_id, user.user_id)

    # Optional Business Rule: nicht löschen, wenn aktive Miete existiert
    if any(r.status == "active" for r in scooter.rentals):
        flash("Scooter kann nicht gelöscht werden: aktive Miete vorhanden.", "warning")
        return redirect(url_for("provider.scooters_list"))

    db.session.delete(scooter)
    db.session.commit()
    flash("Scooter gelöscht.", "success")
    return redirect(url_for("provider.scooters_list"))
