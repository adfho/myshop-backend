from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from decimal import Decimal
from models import db, Order, OrderItem, Product, User, Notification
from routes.cart import read_cart_from_cookie

orders_bp = Blueprint("orders", __name__)

@orders_bp.route("/create", methods=["POST"])
@jwt_required()
def create_order():
    """
    Создание заказа из текущей корзины.
    
    Требует JWT токен. Берет товары из корзины (cookie), для каждого товара:
    - Проверяет наличие в БД
    - Ограничивает количество по stock (остаток на складе)
    - Рассчитывает общую сумму заказа
    - Создает записи Order и OrderItem в БД
    - Уменьшает stock товаров на складе
    - Создает уведомление о создании заказа
    - Очищает корзину (удаляет cookie)
    
    Returns:
        JSON ответ с order_id (201) или ошибкой (400, 401, 404)
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg":"User not found"}), 404
    # Берём корзину из cookie (либо фронтенд пришлёт список)
    cart = read_cart_from_cookie()
    if not cart:
        return jsonify({"msg":"Cart empty"}), 400

    total = Decimal('0.00')
    items = []
    for pid, qty in cart.items():
        product = Product.query.get(pid)
        if not product:
            continue
        if product.stock is not None and qty > product.stock:
            qty = product.stock
        # Преобразуем цену в Decimal если это не Decimal
        price = Decimal(str(product.price))
        line_total = price * qty
        total += line_total
        items.append((product, qty, price))

    if not items:
        return jsonify({"msg":"No valid items to order"}), 400

    # Округляем до 2 знаков после запятой для сохранения в БД
    order = Order(user_id=user_id, total=total.quantize(Decimal('0.01')))
    db.session.add(order)
    db.session.flush()  # получить id

    for product, qty, price in items:
        # Сохраняем цену как Decimal (Numeric в БД)
        oi = OrderItem(order_id=order.id, product_id=product.id, quantity=qty, price=price)
        db.session.add(oi)
        # уменьшить stock если нужно
        if product.stock is not None:
            product.stock = max(0, product.stock - qty)
    # создать уведомление о создании заказа
    notification = Notification(
        user_id=user_id,
        title="Заказ создан",
        message=f"Ваш заказ #{order.id} на сумму {total:.2f} успешно создан",
        type="success"
    )
    db.session.add(notification)
    db.session.commit()

    # очистить cookie корзины — фронтенд должен удалить cookie или сервер может отправить инструкцию
    resp = jsonify({"msg":"Order created", "order_id": order.id})
    resp.set_cookie("cart", "", expires=0)
    return resp, 201

@orders_bp.route("/my", methods=["GET"])
@jwt_required()
def my_orders():
    """
    Получение истории заказов текущего пользователя.
    
    Требует JWT токен. Получает все заказы пользователя, сортирует их
    по дате создания (от новых к старым), для каждого заказа формирует
    список позиций (OrderItem) с данными товаров.
    
    Returns:
        JSON массив заказов с полями id, created_at, total, status, items (200)
        или ошибка авторизации (401)
    """
    user_id = get_jwt_identity()
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
    data = []
    for o in orders:
        items = [{
            "product_id": it.product_id,
            "title": it.product.title,
            "quantity": it.quantity,
            "price": float(it.price) if isinstance(it.price, Decimal) else it.price
        } for it in o.items]
        data.append({
            "id": o.id,
            "created_at": o.created_at.isoformat(),
            "total": float(o.total) if isinstance(o.total, Decimal) else o.total,
            "status": o.status,
            "items": items
        })
    return jsonify(data), 200