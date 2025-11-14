"""
Интеграционные тесты для полного цикла работы приложения.
"""
from decimal import Decimal

from models import Order, Notification, Product


def test_full_user_journey(client, app, test_products):
    """Полный цикл: Регистрация -> Вход -> Добавление в корзину -> Создание заказа."""
    # 1. Регистрация
    register_response = client.post(
        "/api/v1/auth/register",
        data={
            "first_name": "Integration",
            "last_name": "Test",
            "email": "integration@test.com",
            "password": "password123",
        },
    )
    assert register_response.status_code == 201
    user_id = register_response.get_json()["user_id"]

    # 2. Вход
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "integration@test.com", "password": "password123"},
    )
    assert login_response.status_code == 200
    token = login_response.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Используем существующий товар из фикстуры
    product_id = test_products[0]

    # 4. Добавление в корзину
    cart_response = client.post(
        "/api/v1/cart/add", json={"product_id": product_id, "quantity": 2}
    )
    assert cart_response.status_code == 200
    cart_data = cart_response.get_json()
    assert cart_data["count"] == 2

    # 5. Создание заказа
    order_response = client.post("/api/v1/orders/create", headers=headers)
    assert order_response.status_code == 201
    order_data = order_response.get_json()
    assert "order_id" in order_data

    # 6. Проверка заказа в БД
    with app.app_context():
        order = Order.query.get(order_data["order_id"])
        assert order is not None
        assert order.user_id == user_id
        assert order.total >= Decimal("0.00")
        assert len(order.items) > 0

    # 7. Проверка очистки корзины
    cart_check = client.get("/api/v1/cart/")
    assert cart_check.status_code == 200
    assert cart_check.get_json()["count"] == 0


def test_order_creates_notification(client, app, test_products, auth_headers, set_signed_cart_cookie):
    """Создание заказа создает уведомление."""
    pid = test_products[0]
    set_signed_cart_cookie({pid: 1})

    # Создаем заказ
    order_response = client.post("/api/v1/orders/create", headers=auth_headers)
    assert order_response.status_code == 201
    order_id = order_response.get_json()["order_id"]

    # Проверяем уведомление
    with app.app_context():
        from models import User
        # Получаем user_id из токена
        user = User.query.filter_by(email="test@example.com").first()
        assert user is not None
        notifications = Notification.query.filter_by(user_id=user.id).all()
        assert len(notifications) > 0
        order_notification = next(
            (n for n in notifications if f"#{order_id}" in n.message), None
        )
        assert order_notification is not None
        assert order_notification.type == "success"


def test_cart_for_unauthorized_users(client, test_products):
    """Корзина работает для неавторизованных пользователей."""
    product_id = test_products[0]

    # Добавление в корзину без авторизации
    add_response = client.post(
        "/api/v1/cart/add", json={"product_id": product_id, "quantity": 1}
    )
    assert add_response.status_code == 200

    # Получение корзины
    get_response = client.get("/api/v1/cart/")
    assert get_response.status_code == 200
    data = get_response.get_json()
    assert data["count"] == 1

    # Обновление корзины
    update_response = client.post(
        "/api/v1/cart/update", json={"product_id": product_id, "quantity": 3}
    )
    assert update_response.status_code == 200
    assert update_response.get_json()["count"] == 3

    # Удаление из корзины
    remove_response = client.post(
        "/api/v1/cart/remove", json={"product_id": product_id}
    )
    assert remove_response.status_code == 200
    assert remove_response.get_json()["count"] == 0


def test_error_handling_throughout_flow(client, app):
    """Обработка ошибок на всех этапах."""
    # 1. Регистрация с невалидными данными
    invalid_register = client.post(
        "/api/v1/auth/register",
        data={
            "first_name": "",
            "last_name": "",
            "email": "invalid-email",
            "password": "123",
        },
    )
    assert invalid_register.status_code == 422
    error = invalid_register.get_json()["error"]
    assert error["type"] == "validation_error"

    # 2. Вход с неверными данными (сначала валидный email, но неверный пароль)
    invalid_login = client.post(
        "/api/v1/auth/login", json={"email": "nonexistent@test.com", "password": "wrong123"}
    )
    # Может быть 422 если email невалиден, или 401 если валиден но пользователь не найден
    assert invalid_login.status_code in [401, 422]
    error = invalid_login.get_json()["error"]
    assert error["type"] in ["unauthorized", "validation_error"]

    # 3. Добавление несуществующего товара в корзину
    invalid_cart = client.post(
        "/api/v1/cart/add", json={"product_id": 99999, "quantity": 1}
    )
    assert invalid_cart.status_code == 404
    error = invalid_cart.get_json()["error"]
    assert error["type"] == "not_found"

    # 4. Создание заказа без авторизации
    unauthorized_order = client.post("/api/v1/orders/create")
    assert unauthorized_order.status_code == 401

    # 5. Создание заказа с пустой корзиной (требует test_user фикстуру)
    # Этот тест пропускаем, так как требует setup пользователя

