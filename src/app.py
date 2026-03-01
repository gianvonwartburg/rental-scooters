from flask import Flask
from flask import session
from flask import render_template
from dotenv import load_dotenv
from pathlib import Path

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

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=app.config.get("DEBUG", False))
