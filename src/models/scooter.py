from datetime import datetime
from extensions import db


class Scooter(db.Model):
    __tablename__ = "scooters"

    scooter_id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)

    scooter_identifier = db.Column(db.String(64), nullable=False, unique=True)
    status = db.Column(db.String(20), nullable=False)  # available/rented/maintenance
    battery_percent = db.Column(db.Integer, nullable=False)

    latitude = db.Column(db.Numeric(9, 6), nullable=True)
    longitude = db.Column(db.Numeric(9, 6), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    provider = db.relationship("User", backref="scooters")
