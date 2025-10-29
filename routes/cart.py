from flask import Blueprint, request, jsonify, make_response
import json
from models import Product
from decimal import Decimal
from routes.utils import validate_integer

cart_bp = Blueprint("cart", __name__)

def read_cart_from_cookie():
    """
    Читает корзину покупок из cookie браузера.
    
    Извлекает cookie с именем "cart", парсит JSON строку в словарь,
    преобразует ключи и значения в целые числа (product_id -> quantity).
    Если cookie нет или произошла ошибка парсинга, возвращает пустой словарь.
    
    Returns:
        dict: Словарь {product_id: quantity} или {} если корзина пуста/ошибка
    """
    cart_cookie = request.cookies.get("cart")
    if not cart_cookie:
        return {}
    try:
        data = json.loads(cart_cookie)
        if isinstance(data, dict):
            # привести ключи к int
            return {int(k): int(v) for k, v in data.items()}
    except Exception:
        return {}
    return {}

def cart_response(cart_dict):
    """
    Формирует подробный ответ с данными корзины.
    
    Принимает словарь корзины {product_id: quantity} и для каждого товара:
    - Получает данные товара из БД
    - Рассчитывает стоимость позиции (line_total = price * quantity)
    - Суммирует общую стоимость (subtotal и total)
    - Подсчитывает общее количество товаров
    
    Товары, которые не найдены в БД, игнорируются.
    
    Args:
        cart_dict (dict): Словарь {product_id: quantity}
        
    Returns:
        dict: Словарь с полями items, subtotal, total, count
    """
    # соберём подробный ответ: items, subtotal, total, count
    items = []
    subtotal = 0.0
    for pid, qty in cart_dict.items():
        product = Product.query.get(pid)
        if not product:
            continue
        line = {
            "product_id": pid,
            "title": product.title,
            "price": product.price,
            "quantity": qty,
            "line_total": round(product.price * qty, 2)
        }
        subtotal += product.price * qty
        items.append(line)
    return {
        "items": items,
        "subtotal": round(subtotal, 2),
        "total": round(subtotal, 2),  # можно добавить доставку/налоги
        "count": sum([i['quantity'] for i in items])
    }

@cart_bp.route("/", methods=["GET"])
def get_cart():
    """
    Получение содержимого корзины покупок.
    
    Читает корзину из cookie и возвращает подробную информацию:
    список товаров с ценами, общую сумму и количество позиций.
    
    Returns:
        JSON ответ с данными корзины (200)
    """
    cart = read_cart_from_cookie()
    return jsonify(cart_response(cart)), 200

@cart_bp.route("/add", methods=["POST"])
def add_to_cart():
    """
    Добавление товара в корзину.
    
    Принимает JSON с полями:
    - product_id (обязательно, число >= 1) - ID товара
    - quantity (опционально, число >= 1) - Количество (по умолчанию 1)
    
    Валидирует данные, проверяет существование товара, добавляет товар
    в корзину (или увеличивает количество если уже есть), ограничивает
    количество по наличию на складе (stock), сохраняет обновленную корзину в cookie.
    
    Returns:
        JSON ответ с обновленной корзиной (200) или ошибкой (400, 404)
    """
    # body: { "product_id": 1, "quantity": 2 }
    data = request.get_json()
    if not data or "product_id" not in data:
        return jsonify({"msg":"Missing product_id"}), 400
    
    # валидация product_id
    is_valid, pid = validate_integer(data.get("product_id"), "product_id", min_value=1)
    if not is_valid:
        return jsonify({"msg": pid if isinstance(pid, str) else "Invalid product_id"}), 400
    pid = int(pid)
    
    # валидация quantity
    qty = data.get("quantity", 1)
    is_valid, qty = validate_integer(qty, "quantity", min_value=1)
    if not is_valid:
        return jsonify({"msg": qty if isinstance(qty, str) else "Invalid quantity"}), 400
    qty = int(qty)
    product = Product.query.get(pid)
    if not product:
        return jsonify({"msg":"Product not found"}), 404
    cart = read_cart_from_cookie()
    cart[pid] = cart.get(pid, 0) + qty
    # можно ограничить по stock
    if product.stock is not None and cart[pid] > product.stock:
        cart[pid] = product.stock
    resp = make_response(jsonify(cart_response(cart)), 200)
    resp.set_cookie("cart", json.dumps(cart), httponly=False, samesite="Lax")
    return resp

@cart_bp.route("/remove", methods=["POST"])
def remove_from_cart():
    """
    Удаление товара из корзины.
    
    Принимает JSON с полем:
    - product_id (обязательно, число >= 1) - ID товара для удаления
    
    Валидирует product_id, удаляет товар из корзины полностью,
    сохраняет обновленную корзину в cookie.
    
    Returns:
        JSON ответ с обновленной корзиной (200) или ошибка (400)
    """
    data = request.get_json()
    if not data or "product_id" not in data:
        return jsonify({"msg":"Missing product_id"}), 400
    
    is_valid, pid = validate_integer(data.get("product_id"), "product_id", min_value=1)
    if not is_valid:
        return jsonify({"msg": pid if isinstance(pid, str) else "Invalid product_id"}), 400
    pid = int(pid)
    cart = read_cart_from_cookie()
    if pid in cart:
        cart.pop(pid)
    resp = make_response(jsonify(cart_response(cart)), 200)
    resp.set_cookie("cart", json.dumps(cart), httponly=False, samesite="Lax")
    return resp

@cart_bp.route("/update", methods=["POST"])
def update_cart():
    """
    Обновление количества товара в корзине.
    
    Принимает JSON с полями:
    - product_id (обязательно, число >= 1) - ID товара
    - quantity (обязательно, число >= 0) - Новое количество
    
    Валидирует данные, если quantity <= 0, товар удаляется из корзины,
    иначе обновляет количество (ограничивая по stock), сохраняет в cookie.
    
    Returns:
        JSON ответ с обновленной корзиной (200) или ошибкой (400, 404)
    """
    data = request.get_json()
    # body: { "product_id":1, "quantity":3 }
    if not data or "product_id" not in data or "quantity" not in data:
        return jsonify({"msg":"Missing fields"}), 400
    
    is_valid, pid = validate_integer(data.get("product_id"), "product_id", min_value=1)
    if not is_valid:
        return jsonify({"msg": pid if isinstance(pid, str) else "Invalid product_id"}), 400
    pid = int(pid)
    
    is_valid, qty = validate_integer(data.get("quantity"), "quantity", min_value=0)
    if not is_valid:
        return jsonify({"msg": qty if isinstance(qty, str) else "Invalid quantity"}), 400
    qty = int(qty)
    product = Product.query.get(pid)
    if not product:
        return jsonify({"msg":"Product not found"}), 404
    cart = read_cart_from_cookie()
    if qty <= 0:
        cart.pop(pid, None)
    else:
        # check stock
        if product.stock is not None and qty > product.stock:
            qty = product.stock
        cart[pid] = qty
    resp = make_response(jsonify(cart_response(cart)), 200)
    resp.set_cookie("cart", json.dumps(cart), httponly=False, samesite="Lax")
    return resp