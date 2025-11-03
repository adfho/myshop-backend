"""
Конфигурация pytest для тестов Flask приложения.
"""
import pytest
from app import create_app
from models import db, User, Category, Product
from decimal import Decimal


@pytest.fixture
def app():
    """Создает тестовое приложение Flask."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['JWT_SECRET_KEY'] = 'test-jwt-secret-key'
    app.config['IS_PRODUCTION'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Создает тестовый клиент Flask."""
    return app.test_client()


@pytest.fixture
def test_user(app):
    """Создает тестового пользователя."""
    with app.app_context():
        user = User(
            first_name="Test",
            last_name="User",
            email="test@example.com"
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def test_category(app):
    """Создает тестовую категорию."""
    with app.app_context():
        category = Category(name="Electronics")
        db.session.add(category)
        db.session.commit()
        # Сохраняем ID перед выходом из контекста
        category_id = category.id
        db.session.expunge(category)  # Отсоединяем от сессии
        return category_id  # Возвращаем ID вместо объекта


@pytest.fixture
def test_products(app, test_category):
    """Создает тестовые товары."""
    with app.app_context():
        # test_category теперь это ID
        category_id = test_category if isinstance(test_category, int) else test_category.id
        products = [
            Product(
                title="Smartphone",
                description="Good phone",
                price=Decimal("299.99"),
                stock=10,
                category_id=category_id
            ),
            Product(
                title="Laptop",
                description="Work laptop",
                price=Decimal("899.00"),
                stock=5,
                category_id=category_id
            )
        ]
        for product in products:
            db.session.add(product)
        db.session.commit()
        # Сохраняем ID перед выходом
        product_ids = [p.id for p in products]
        return product_ids  # Возвращаем список ID


@pytest.fixture
def auth_headers(client, test_user):
    """Возвращает заголовки авторизации для тестов."""
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    data = response.get_json()
    token = data['access_token']
    return {'Authorization': f'Bearer {token}'}

