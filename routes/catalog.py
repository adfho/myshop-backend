from flask import Blueprint, request, jsonify, current_app
from models import Product, Category, db
from sqlalchemy.orm import selectinload
from errors import NotFoundError
from extensions import cache

catalog_bp = Blueprint("catalog", __name__)

@catalog_bp.route("/products", methods=["GET"])
@cache.cached(timeout=60, query_string=True)  # Кэш на 1 минуту с учетом query параметров
def list_products():
    """
    Получение списка товаров с фильтрацией и сортировкой.
    
    Параметры запроса (query string):
    - q (опционально, строка) - Поисковый запрос (поиск по названию товара)
    - category (опционально, число) - ID категории для фильтрации
    - min_price (опционально, число) - Минимальная цена товара
    - max_price (опционально, число) - Максимальная цена товара
    - sort (опционально, строка) - Тип сортировки:
      price_asc, price_desc, title_asc, title_desc, id_desc
    - page (опционально, число) - Номер страницы (по умолчанию 1)
    - per_page (опционально, число) - Товаров на странице (по умолчанию 12)
    
    Применяет фильтры по поисковому запросу, категории и цене, сортирует товары,
    возвращает пагинированный список.
    
    Returns:
        JSON ответ с items (список товаров), total, page, pages (200)
    """
    # параметры: ?q=search&category=1&min_price=10&max_price=100
    # &sort=price_asc&page=1&per_page=10
    q = request.args.get("q", type=str)
    category = request.args.get("category", type=int)
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    sort = request.args.get("sort", default="id_desc", type=str)
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=12, type=int)

    query = Product.query.options(selectinload(Product.category))

    if q:
        query = query.filter(Product.title.ilike(f"%{q}%"))
    if category:
        query = query.filter_by(category_id=category)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    if sort == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price.desc())
    elif sort == "title_asc":
        query = query.order_by(Product.title.asc())
    elif sort == "title_desc":
        query = query.order_by(Product.title.desc())
    else:
        query = query.order_by(Product.id.desc())

    pag = query.paginate(page=page, per_page=per_page, error_out=False)
    items = [{
        "id": p.id,
        "title": p.title,
        "description": p.description,
        "price": p.price,
        "stock": p.stock,
        "image": p.image,
        "category_id": p.category_id,
        "category_name": p.category.name if p.category else None
    } for p in pag.items]

    return jsonify({
        "items": items,
        "total": pag.total,
        "page": pag.page,
        "pages": pag.pages
    }), 200

@catalog_bp.route("/categories", methods=["GET"])
@cache.cached(timeout=300, key_prefix="categories_list")  # Кэш на 5 минут
def list_categories():
    """
    Получение списка всех категорий товаров.
    
    Возвращает все категории из базы данных с их ID и названиями.
    Результат кэшируется на 5 минут.
    
    Returns:
        JSON массив категорий с полями id и name (200)
    """
    cats = Category.query.all()
    return jsonify([{"id":c.id,"name":c.name} for c in cats]), 200

@catalog_bp.route("/products/<int:product_id>", methods=["GET"])
def product_detail(product_id):
    """
    Получение детальной информации о конкретном товаре.
    
    Args:
        product_id (int): ID товара
        
    Returns:
        JSON объект с полными данными товара (200) или ошибка 404 если товар не найден
    """
    p = (
        Product.query.options(selectinload(Product.category))
        .filter_by(id=product_id)
        .first()
    )
    if not p:
        raise NotFoundError("Product not found")
    return jsonify({
        "id": p.id,
        "title": p.title,
        "description": p.description,
        "price": p.price,
        "stock": p.stock,
        "image": p.image,
        "category_id": p.category_id,
        "category_name": p.category.name if p.category else None
    }), 200