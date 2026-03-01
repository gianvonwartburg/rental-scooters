from functools import wraps
import secrets

from flask import Blueprint, g, jsonify, request
from werkzeug.security import check_password_hash

from extensions import db
from models import ApiToken, Rental, Scooter, User

api_bp = Blueprint("api", __name__, url_prefix="/api")


def parse_bearer_token(header_value: str | None) -> str | None:
    if not header_value:
        return None
    parts = header_value.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1]


def api_auth_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token_value = parse_bearer_token(request.headers.get("Authorization"))
        if not token_value:
            return jsonify({"error": "unauthorized"}), 401

        token = ApiToken.query.filter_by(token=token_value).first()
        if not token:
            return jsonify({"error": "unauthorized"}), 401

        g.api_user = token.user
        return fn(*args, **kwargs)

    return wrapper


def _to_float(value):
    return float(value) if value is not None else None


def _to_iso(dt):
    return dt.isoformat() if dt is not None else None


def _generate_unique_token() -> str:
    while True:
        token_value = secrets.token_urlsafe(32)
        exists = ApiToken.query.filter_by(token=token_value).first()
        if not exists:
            return token_value


@api_bp.post("/auth/token")
def create_token():
    data = request.get_json(silent=True) or {}

    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"error": "bad_request"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "invalid_credentials"}), 401

    token_value = _generate_unique_token()
    api_token = ApiToken(user_id=user.user_id, token=token_value)
    db.session.add(api_token)
    db.session.commit()

    return jsonify({"access_token": token_value, "token_type": "Bearer"}), 200


@api_bp.get("/scooters")
@api_auth_required
def scooters_list_api():
    scooters = Scooter.query.order_by(Scooter.created_at.desc()).all()
    payload = [
        {
            "scooter_id": scooter.scooter_id,
            "scooter_identifier": scooter.scooter_identifier,
            "status": scooter.status,
            "battery_percent": scooter.battery_percent,
            "latitude": _to_float(scooter.latitude),
            "longitude": _to_float(scooter.longitude),
            "provider_id": scooter.provider_id,
            "created_at": _to_iso(scooter.created_at),
        }
        for scooter in scooters
    ]
    return jsonify(payload), 200


@api_bp.get("/rentals/me")
@api_auth_required
def my_rentals_api():
    if g.api_user.role != "driver":
        return jsonify({"error": "forbidden"}), 403

    rentals = (
        Rental.query.filter_by(driver_id=g.api_user.user_id)
        .order_by(Rental.start_time.desc())
        .all()
    )
    payload = [
        {
            "rental_id": rental.rental_id,
            "scooter_id": rental.scooter_id,
            "start_time": _to_iso(rental.start_time),
            "end_time": _to_iso(rental.end_time),
            "distance_km": _to_float(rental.distance_km),
            "billed_minutes": rental.billed_minutes,
            "price_total": _to_float(rental.price_total),
            "status": rental.status,
        }
        for rental in rentals
    ]
    return jsonify(payload), 200
