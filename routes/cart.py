from flask import Blueprint, request, jsonify, make_response
import json
from models import Product
from decimal import Decimal

cart_bp = Blueprint("cart", __name__)

def read_cart_from_cookie():
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
    cart = read_cart_from_cookie()
    return jsonify(cart_response(cart)), 200

@cart_bp.route("/add", methods=["POST"])
def add_to_cart():
    # body: { "product_id": 1, "quantity": 2 }
    data = request.get_json()
    if not data or "product_id" not in data:
        return jsonify({"msg":"Missing product_id"}), 400
    pid = int(data["product_id"])
    qty = int(data.get("quantity", 1))
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
    data = request.get_json()
    if not data or "product_id" not in data:
        return jsonify({"msg":"Missing product_id"}), 400
    pid = int(data["product_id"])
    cart = read_cart_from_cookie()
    if pid in cart:
        cart.pop(pid)
    resp = make_response(jsonify(cart_response(cart)), 200)
    resp.set_cookie("cart", json.dumps(cart), httponly=False, samesite="Lax")
    return resp

@cart_bp.route("/update", methods=["POST"])
def update_cart():
    data = request.get_json()
    # body: { "product_id":1, "quantity":3 }
    if not data or "product_id" not in data or "quantity" not in data:
        return jsonify({"msg":"Missing fields"}), 400
    pid = int(data["product_id"])
    qty = int(data["quantity"])
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