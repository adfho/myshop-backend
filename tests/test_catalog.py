"""
Тесты для каталога товаров.
"""


def test_list_products(client, test_products):
    """Тест получения списка товаров."""
    response = client.get('/api/catalog/products')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'items' in data
    assert 'total' in data
    assert 'page' in data
    assert len(data['items']) >= 2  # У нас 2 тестовых товара


def test_list_products_with_filter(client, test_products, test_category):
    """Тест фильтрации товаров по категории."""
    category_id = test_category if isinstance(test_category, int) else test_category.id
    response = client.get(f'/api/catalog/products?category={category_id}')
    
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['items']) >= 2
    for item in data['items']:
        assert item['category_id'] == category_id


def test_list_products_price_filter(client, test_products):
    """Тест фильтрации по цене."""
    response = client.get('/api/catalog/products?min_price=300&max_price=500')
    
    assert response.status_code == 200
    data = response.get_json()
    for item in data['items']:
        assert 300 <= item['price'] <= 500


def test_list_products_search(client, test_products):
    """Тест поиска товаров."""
    response = client.get('/api/catalog/products?q=smartphone')
    
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['items']) >= 1
    assert any('smartphone' in item['title'].lower() for item in data['items'])


def test_list_products_pagination(client, test_products):
    """Тест пагинации."""
    response = client.get('/api/catalog/products?page=1&per_page=1')
    
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['items']) == 1
    assert data['pages'] >= 2


def test_list_categories(client, test_category):
    """Тест получения списка категорий."""
    response = client.get('/api/catalog/categories')
    
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(cat['name'] == 'Electronics' for cat in data)


def test_product_detail(client, test_products, app):
    """Тест получения деталей товара."""
    from models import Product
    product_id = test_products[0] if isinstance(test_products[0], int) else test_products[0].id
    response = client.get(f'/api/catalog/products/{product_id}')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['id'] == product_id
    # Проверяем что товар существует
    with app.app_context():
        product = Product.query.get(product_id)
        assert product is not None
        assert data['title'] == product.title


def test_product_detail_not_found(client):
    """Тест получения несуществующего товара."""
    response = client.get('/api/catalog/products/99999')
    
    assert response.status_code == 404
    data = response.get_json()
    assert 'not found' in data['msg'].lower()

