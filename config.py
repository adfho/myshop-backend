import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Определяем окружение: 'production', 'development', 'testing'
    ENV = os.environ.get("FLASK_ENV", "development")
    IS_PRODUCTION = ENV == "production"
    
    # В проде секреты ОБЯЗАТЕЛЬНЫ из окружения, иначе приложение не запустится
    if IS_PRODUCTION:
        SECRET_KEY = os.environ.get("SECRET_KEY")
        JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
        if not SECRET_KEY or not JWT_SECRET_KEY:
            raise ValueError(
                "В production окружении SECRET_KEY и JWT_SECRET_KEY должны быть заданы "
                "через переменные окружения!"
            )
    else:
        # Для dev/test используем значения по умолчанию
        SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
        JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-secret-string-change-in-production")
    
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or \
        "sqlite:///" + os.path.join(basedir, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, "static", "avatars")
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB max avatar
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

    APP_VERSION = os.environ.get("APP_VERSION", "0.1.0")

    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_DIR = os.environ.get("LOG_DIR", os.path.join(basedir, "logs"))
    LOG_MAX_BYTES = int(os.environ.get("LOG_MAX_BYTES", 5 * 1024 * 1024))
    LOG_BACKUP_COUNT = int(os.environ.get("LOG_BACKUP_COUNT", 5))

    RATE_LIMIT_GENERAL = os.environ.get("RATE_LIMIT_GENERAL", "300 per minute")
    RATE_LIMIT_DEFAULT = os.environ.get("RATE_LIMIT_DEFAULT", RATE_LIMIT_GENERAL)
    RATE_LIMIT_AUTH = os.environ.get("RATE_LIMIT_AUTH", "5 per minute")
    RATE_LIMIT_STORAGE_URI = os.environ.get("RATE_LIMIT_STORAGE_URI", "memory://")
    RATELIMIT_ENABLED = os.environ.get("RATELIMIT_ENABLED", "true").lower() == "true"

    # Кэширование
    CACHE_TYPE = os.environ.get("CACHE_TYPE", "SimpleCache")
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get("CACHE_DEFAULT_TIMEOUT", 300))  # 5 минут
    CACHE_REDIS_URL = os.environ.get("CACHE_REDIS_URL")  # redis://localhost:6379/0