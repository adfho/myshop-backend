from flask import Blueprint, request, jsonify
from models import db, Product, Category

catalog_bp = Blueprint("catalog", __name__)

@catalog_bp.route("/products", methods=["GET"])
def list_products():
    # параметры: ?q=search&category=1&min_price=10&max_price=100&sort=price_asc&page=1&per_page=10
    q = request.args.get("q", type=str)
    category = request.args.get("category", type=int)
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    sort = request.args.get("sort", default="id_desc", type=str)
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=12, type=int)

    query = Product.query

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
        "category_id": p.category_id
    } for p in pag.items]

    return jsonify({
        "items": items,
        "total": pag.total,
        "page": pag.page,
        "pages": pag.pages
    }), 200

@catalog_bp.route("/categories", methods=["GET"])
def list_categories():
    cats = Category.query.all()
    return jsonify([{"id":c.id,"name":c.name} for c in cats]), 200

@catalog_bp.route("/products/<int:product_id>", methods=["GET"])
def product_detail(product_id):
    p = Product.query.get(product_id)
    if not p:
        return jsonify({"msg":"Product not found"}), 404
    return jsonify({
        "id": p.id,
        "title": p.title,
        "description": p.description,
        "price": p.price,
        "stock": p.stock,
        "image": p.image,
        "category_id": p.category_id
    }), 200