"""
Тесты для авторизации и регистрации пользователей.
"""
from models import User


def test_register_user(client, app):
    """Тест регистрации нового пользователя."""
    response = client.post('/api/v1/auth/register', data={
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john@example.com',
        'password': 'password123'
    })
    
    assert response.status_code == 201
    data = response.get_json()
    assert 'user_id' in data
    assert data['msg'] == 'User created'
    
    # Проверяем что пользователь создан в БД
    with app.app_context():
        user = User.query.filter_by(email='john@example.com').first()
        assert user is not None
        assert user.first_name == 'John'
        assert user.last_name == 'Doe'
        assert user.check_password('password123')


def test_register_duplicate_email(client, test_user):
    """Тест регистрации с существующим email."""
    response = client.post('/api/v1/auth/register', data={
        'first_name': 'Another',
        'last_name': 'User',
        'email': 'test@example.com',  # Уже существует
        'password': 'password123'
    })
    
    assert response.status_code == 409
    data = response.get_json()
    assert data['error']['type'] == 'conflict'
    assert 'already exists' in data['error']['message'].lower()


def test_register_invalid_email(client):
    """Тест регистрации с невалидным email."""
    response = client.post('/api/v1/auth/register', data={
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'invalid-email',
        'password': 'password123'
    })
    
    assert response.status_code == 422
    data = response.get_json()
    assert data['error']['type'] == 'validation_error'
    assert 'invalid email format' in data['error']['message'].lower()


def test_register_short_password(client):
    """Тест регистрации с коротким паролем."""
    response = client.post('/api/v1/auth/register', data={
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john@example.com',
        'password': '12345'  # Меньше 6 символов
    })
    
    assert response.status_code == 422
    data = response.get_json()
    assert data['error']['type'] == 'validation_error'
    assert 'password' in data['error']['message'].lower()


def test_login_success(client, test_user):
    """Тест успешного входа."""
    response = client.post('/api/v1/auth/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'access_token' in data
    assert 'user' in data
    assert data['user']['email'] == 'test@example.com'


def test_login_wrong_password(client, test_user):
    """Тест входа с неверным паролем."""
    response = client.post('/api/v1/auth/login', json={
        'email': 'test@example.com',
        'password': 'wrongpassword'
    })
    
    assert response.status_code == 401
    data = response.get_json()
    assert data['error']['type'] == 'unauthorized'
    assert 'bad email or password' in data['error']['message'].lower()


def test_login_nonexistent_user(client):
    """Тест входа несуществующего пользователя."""
    response = client.post('/api/v1/auth/login', json={
        'email': 'nonexistent@example.com',
        'password': 'password123'
    })
    
    assert response.status_code == 401
    data = response.get_json()
    assert data['error']['type'] == 'unauthorized'
    assert 'bad email or password' in data['error']['message'].lower()


def test_me_endpoint(client, auth_headers, test_user):
    """Тест получения данных текущего пользователя."""
    response = client.get('/api/v1/auth/me', headers=auth_headers)
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['email'] == 'test@example.com'
    assert data['first_name'] == 'Test'
    assert data['last_name'] == 'User'
    assert 'unread_notifications' in data


def test_me_endpoint_unauthorized(client):
    """Тест доступа к /me без авторизации."""
    response = client.get('/api/v1/auth/me')
    
    assert response.status_code == 401

