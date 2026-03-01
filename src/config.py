import os
from pathlib import Path

# config.py liegt in src/
BASE_DIR = Path(__file__).resolve().parent.parent  # -> Repo-Root
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)

DEFAULT_SQLITE_PATH = INSTANCE_DIR / "app.db"


def _get_bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "t", "yes", "y", "on"}


class Config:
    DEBUG = _get_bool_env("FLASK_DEBUG", default=False)
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY and not DEBUG:
        raise RuntimeError(
            "SECRET_KEY environment variable is required when FLASK_DEBUG is false."
        )

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = not DEBUG

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
