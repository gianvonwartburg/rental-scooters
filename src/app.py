from flask import Flask
from flask import session
from flask import render_template
from dotenv import load_dotenv
from pathlib import Path
import os

# .env aus Repo-Root laden am Anfang
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

from config import Config
from extensions import db
from models import ApiToken, Rental, Scooter, User

from routes.auth import auth_bp
from routes.api import api_bp
from routes.provider import provider_bp
from routes.driver import driver_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(provider_bp)
    app.register_blueprint(driver_bp)

    @app.context_processor
    def inject_user():
        user_id = session.get("user_id")
        if not user_id:
            return {"current_user": None}
        user = db.session.get(User, user_id)
        return {"current_user": user}
    
    @app.route("/")
    def home():
        return render_template("home.html")    

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500
    
    with app.app_context():
        if os.getenv("INIT_DB") == "1":
            db.create_all()

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=app.config.get("DEBUG", False))
