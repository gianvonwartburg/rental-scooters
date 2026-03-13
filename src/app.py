from flask import Flask, session, render_template
from dotenv import load_dotenv
from pathlib import Path
import os
import time

if Path(__file__).resolve().parent.parent.joinpath(".env").exists():
    load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

from config import Config
from extensions import db
from models import User

from routes.auth import auth_bp
from routes.api import api_bp
from routes.provider import provider_bp
from routes.driver import driver_bp

def create_app():
    start = time.perf_counter()
    print("startup: create_app start", flush=True)

    app = Flask(__name__)
    print(f"startup: Flask created after {time.perf_counter() - start:.3f}s", flush=True)

    app.config.from_object(Config)
    print(f"startup: config loaded after {time.perf_counter() - start:.3f}s", flush=True)

    db.init_app(app)
    print(f"startup: db.init_app done after {time.perf_counter() - start:.3f}s", flush=True)

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(provider_bp)
    app.register_blueprint(driver_bp)
    print(f"startup: blueprints registered after {time.perf_counter() - start:.3f}s", flush=True)

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
        print(f"startup: app_context entered after {time.perf_counter() - start:.3f}s", flush=True)
        if os.getenv("INIT_DB") == "1":
            print("startup: INIT_DB=1 -> db.create_all start", flush=True)
            db.create_all()
            print(f"startup: db.create_all done after {time.perf_counter() - start:.3f}s", flush=True)

    print(f"startup: create_app done after {time.perf_counter() - start:.3f}s", flush=True)
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=app.config.get("DEBUG", False))
