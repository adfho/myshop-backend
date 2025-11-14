"""
Тесты для заказов.
"""
from decimal import Decimal

from models import Order


def test_create_order_clears_cart(
    client, test_user, test_products, auth_headers, set_signed_cart_cookie, app
):
    """Создание заказа очищает корзину и возвращает корректный ответ."""
    pid1, pid2 = test_products
    set_signed_cart_cookie({pid1: 2, pid2: 1})

    response = client.post('/api/v1/orders/create', headers=auth_headers)

    assert response.status_code == 201
    data = response.get_json()
    assert 'order_id' in data

    set_cookie_header = ";".join(response.headers.getlist('Set-Cookie'))
    assert 'cart=' in set_cookie_header
    assert 'expires=' in set_cookie_header.lower()

    cart_state = client.get('/api/v1/cart/')
    assert cart_state.status_code == 200
    assert cart_state.get_json()['count'] == 0

    with app.app_context():
        order = Order.query.get(data['order_id'])
        assert order is not None
        assert order.total >= Decimal('0.00')


def test_create_order_requires_auth(client):
    """Создание заказа без токена отклоняется."""
    response = client.post('/api/v1/orders/create')
    assert response.status_code == 401


def test_my_orders_returns_results(
    client, auth_headers, test_products, set_signed_cart_cookie
):
    """Получение заказов возвращает список после создания заказа."""
    set_signed_cart_cookie({test_products[0]: 1})
    client.post('/api/v1/orders/create', headers=auth_headers)

    response = client.get('/api/v1/orders/my', headers=auth_headers)

    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    if data:
        first = data[0]
        assert 'id' in first
        assert isinstance(first['items'], list)


def test_my_orders_unauthorized(client):
    """Получение заказов без токена возвращает 401."""
    response = client.get('/api/v1/orders/my')
    assert response.status_code == 401

