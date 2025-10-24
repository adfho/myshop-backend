import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or \
        "sqlite:///" + os.path.join(basedir, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-secret-string")
    UPLOAD_FOLDER = os.path.join(basedir, "static", "avatars")
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB max avatar
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}