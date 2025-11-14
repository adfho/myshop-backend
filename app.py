import os
import time
from flask import Flask, g, request, got_request_exception, has_request_context
from config import Config
from models import db
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
from extensions import limiter, cache
from logging_config import setup_logging
from errors import register_error_handlers

def create_app():
    """
    Фабрика приложения Flask.
    
    Создает и настраивает Flask приложение:
    - Инициализирует конфигурацию из Config
    - Создает папку для загрузки аватаров
    - Подключает базу данных (SQLAlchemy)
    - Настраивает JWT для аутентификации
    - Настраивает CORS для работы с фронтендом (разрешает cookies)
    - Регистрирует все маршруты API (auth, catalog, cart, orders)
    - Создает все таблицы в базе данных если их нет
    
    Returns:
        Flask: Настроенное Flask приложение
    """
    app = Flask(__name__)
    app.config.from_object(Config)
    setup_logging(app)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    app.config.setdefault("RATELIMIT_STORAGE_URI", app.config["RATE_LIMIT_STORAGE_URI"])
    app.config.setdefault("RATELIMIT_DEFAULT", [app.config["RATE_LIMIT_DEFAULT"]])
    limiter.init_app(app)
    limiter.enabled = app.config.get("RATELIMIT_ENABLED", True)
    
    # Настройка кэширования
    cache_config = {"CACHE_TYPE": app.config.get("CACHE_TYPE", "SimpleCache")}
    if app.config.get("CACHE_REDIS_URL"):
        cache_config["CACHE_TYPE"] = "RedisCache"
        cache_config["CACHE_REDIS_URL"] = app.config["CACHE_REDIS_URL"]
    cache.init_app(app, config=cache_config)
    # Инициализация Flask-Migrate (не сохраняем в переменную, используется для регистрации)
    Migrate(app, db)
    # Инициализация JWT (не сохраняем в переменную, используется для регистрации)
    JWTManager(app)
    CORS(app, supports_credentials=True)  # разрешаем куки/credentials если фронтенд с другим origin

    # импорт и регистрация роутов
    from routes.auth import auth_bp
    from routes.catalog import catalog_bp
    from routes.cart import cart_bp
    from routes.orders import orders_bp
    from routes.health import health_bp
    # API версионирование: все эндпоинты под /api/v1/
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(catalog_bp, url_prefix="/api/v1/catalog")
    app.register_blueprint(cart_bp, url_prefix="/api/v1/cart")
    app.register_blueprint(orders_bp, url_prefix="/api/v1/orders")
    app.register_blueprint(health_bp)
    register_error_handlers(app)

    @app.before_request
    def start_request_timer():
        g.request_start_time = time.perf_counter()

    @app.after_request
    def log_request(response):
        duration_ms = None
        if hasattr(g, "request_start_time"):
            duration_ms = round((time.perf_counter() - g.request_start_time) * 1000, 2)
        app.logger.info(
            "http_request",
            extra={
                "event": "http_request",
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
                "remote_addr": request.headers.get("X-Forwarded-For", request.remote_addr),
            },
        )
        return response

    def log_exception(sender, exception, **extra):
        path = request.path if has_request_context() else None
        method = request.method if has_request_context() else None
        sender.logger.exception(
            "application_error",
            extra={
                "event": "application_error",
                "path": path,
                "method": method,
            },
        )

    got_request_exception.connect(log_exception, app)

    # НЕ создаём БД автоматически - используем миграции Flask-Migrate
    # Для инициализации: flask db init, flask db migrate, flask db upgrade

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)