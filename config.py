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