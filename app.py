import os
from flask import Flask
from config import Config
from models import db
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate

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
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
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
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(catalog_bp, url_prefix="/api/catalog")
    app.register_blueprint(cart_bp, url_prefix="/api/cart")
    app.register_blueprint(orders_bp, url_prefix="/api/orders")

    # НЕ создаём БД автоматически - используем миграции Flask-Migrate
    # Для инициализации: flask db init, flask db migrate, flask db upgrade

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)