import os
from pathlib import Path

# config.py liegt in src/
BASE_DIR = Path(__file__).resolve().parent.parent  # -> Repo-Root
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)

DEFAULT_SQLITE_PATH = INSTANCE_DIR / "app.db"

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False