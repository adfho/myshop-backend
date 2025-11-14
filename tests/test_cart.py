import json
from http.cookies import SimpleCookie

from itsdangerous import BadSignature, URLSafeSerializer
from models import db, Product


def _extract_cookie_value(response, name):
    cookies = SimpleCookie()
    for header in response.headers.getlist('Set-Cookie'):
        cookies.load(header)
    morsel = cookies.get(name)
    return morsel.value if morsel else None


def test_add_to_cart_sets_signed_cookie(client, test_products, app):
    product_id = test_products[0]
    response = client.post('/api/v1/cart/add', json={"product_id": product_id, "quantity": 2})

    assert response.status_code == 200
    data = response.get_json()
    assert data['count'] == 2

    cookie_value = _extract_cookie_value(response, 'cart')
    assert cookie_value is not None
    signer = URLSafeSerializer(app.config['SECRET_KEY'])
    payload = json.loads(signer.loads(cookie_value))
    assert str(product_id) in payload


def test_cart_rejects_tampered_cookie(client):
    client.set_cookie("cart", "tampered")
    response = client.get('/api/v1/cart/')
    assert response.status_code == 200
    data = response.get_json()
    assert data['count'] == 0


def test_cart_valid_cookie_signature(client, test_products, app):
    product_id = test_products[0]
    response = client.post('/api/v1/cart/add', json={"product_id": product_id})
    cookie_value = _extract_cookie_value(response, 'cart')
    signer = URLSafeSerializer(app.config['SECRET_KEY'])
    try:
        signer.loads(cookie_value)
    except BadSignature:
        assert False, "Cookie signature must be valid"


def test_add_to_cart_out_of_stock(client, test_products, app):
    product_id = test_products[0]
    with app.app_context():
        product = Product.query.get(product_id)
        product.stock = 1
        db.session.commit()

    response = client.post('/api/v1/cart/add', json={"product_id": product_id, "quantity": 5})
    assert response.status_code == 422
    error = response.get_json()['error']
    assert error['type'] == 'validation_error'
    assert 'only' in error['message'].lower()


def test_update_cart_checks_stock(client, test_products, app):
    product_id = test_products[0]
    with app.app_context():
        product = Product.query.get(product_id)
        product.stock = 1
        db.session.commit()

    client.post('/api/v1/cart/add', json={"product_id": product_id})
    response = client.post('/api/v1/cart/update', json={"product_id": product_id, "quantity": 2})

    assert response.status_code == 422
    error = response.get_json()['error']
    assert error['type'] == 'validation_error'


def test_remove_from_cart(client, test_products):
    product_id = test_products[0]
    client.post('/api/v1/cart/add', json={"product_id": product_id})
    response = client.post('/api/v1/cart/remove', json={"product_id": product_id})
    assert response.status_code == 200
    assert response.get_json()['count'] == 0

