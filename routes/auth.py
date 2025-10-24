from flask import Blueprint, request, jsonify, current_app, send_from_directory
from models import db, User
from routes.utils import save_avatar, allowed_file
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import os

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.form.to_dict()
    # ожидаем first_name, last_name, email, password; avatar optional (multipart/form-data)
    email = data.get("email")
    if not email or not data.get("password") or not data.get("first_name") or not data.get("last_name"):
        return jsonify({"msg":"Missing fields"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"msg":"User already exists"}), 409

    user = User(first_name=data["first_name"], last_name=data["last_name"], email=email)
    user.set_password(data["password"])

    if "avatar" in request.files:
        f = request.files["avatar"]
        saved = save_avatar(f)
        if saved is None:
            return jsonify({"msg":"Invalid avatar extension"}), 400
        user.avatar = saved

    db.session.add(user)
    db.session.commit()
    return jsonify({"msg":"User created", "user_id": user.id}), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"msg":"Missing credentials"}), 400
    user = User.query.filter_by(email=data["email"]).first()
    if not user or not user.check_password(data["password"]):
        return jsonify({"msg":"Bad email or password"}), 401
    access_token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": access_token, "user": {
        "id": user.id, "first_name": user.first_name, "last_name": user.last_name,
        "email": user.email, "avatar": user.avatar
    }}), 200

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg":"User not found"}), 404
    # история заказов и уведомления можно вытягивать здесь или отдельным эндпоинтом (см orders)
    return jsonify({
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "avatar": user.avatar
    }), 200

# endpoint to serve avatars (если фронтенд не будет напрямую брать static)
@auth_bp.route("/avatar/<filename>", methods=["GET"])
def avatar(filename):
    folder = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(folder, filename)