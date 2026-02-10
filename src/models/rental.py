from datetime import datetime
from extensions import db


class Rental(db.Model):
    __tablename__ = "rentals"

    rental_id = db.Column(db.Integer, primary_key=True)
    scooter_id = db.Column(db.Integer, db.ForeignKey("scooters.scooter_id"), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)

    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)

    distance_km = db.Column(db.Numeric(8, 2), nullable=True)
    price_total = db.Column(db.Numeric(10, 2), nullable=True)

    status = db.Column(db.String(20), nullable=False)  # active/finished/cancelled

    scooter = db.relationship("Scooter", backref="rentals")
    driver = db.relationship("User", backref="rentals")
