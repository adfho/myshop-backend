from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Order, OrderItem, Product, User
from routes.cart import read_cart_from_cookie

orders_bp = Blueprint("orders", __name__)

@orders_bp.route("/create", methods=["POST"])
@jwt_required()
def create_order():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg":"User not found"}), 404
    # Берём корзину из cookie (либо фронтенд пришлёт список)
    cart = read_cart_from_cookie()
    if not cart:
        return jsonify({"msg":"Cart empty"}), 400

    total = 0.0
    items = []
    for pid, qty in cart.items():
        product = Product.query.get(pid)
        if not product:
            continue
        if product.stock is not None and qty > product.stock:
            qty = product.stock
        line_total = product.price * qty
        total += line_total
        items.append((product, qty, product.price))

    if not items:
        return jsonify({"msg":"No valid items to order"}), 400

    order = Order(user_id=user_id, total=round(total, 2))
    db.session.add(order)
    db.session.flush()  # получить id

    for product, qty, price in items:
        oi = OrderItem(order_id=order.id, product_id=product.id, quantity=qty, price=price)
        db.session.add(oi)
        # уменьшить stock если нужно
        if product.stock is not None:
            product.stock = max(0, product.stock - qty)
    db.session.commit()

    # очистить cookie корзины — фронтенд должен удалить cookie или сервер может отправить инструкцию
    resp = jsonify({"msg":"Order created", "order_id": order.id})
    resp.set_cookie("cart", "", expires=0)
    return resp, 201

@orders_bp.route("/my", methods=["GET"])
@jwt_required()
def my_orders():
    user_id = get_jwt_identity()
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
    data = []
    for o in orders:
        items = [{
            "product_id": it.product_id,
            "title": it.product.title,
            "quantity": it.quantity,
            "price": it.price
        } for it in o.items]
        data.append({
            "id": o.id,
            "created_at": o.created_at.isoformat(),
            "total": o.total,
            "status": o.status,
            "items": items
        })
    return jsonify(data), 200