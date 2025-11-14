from flask import Blueprint, request, jsonify, current_app, send_from_directory
from models import db, User, Notification
from routes.utils import save_avatar
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from extensions import limiter
from schemas import RegisterSchema, LoginSchema
from errors import ConflictError, UnauthorizedError, NotFoundError

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
@limiter.limit(lambda: current_app.config["RATE_LIMIT_AUTH"])
def register():
    """
    Регистрация нового пользователя.
    
    Принимает данные формы (multipart/form-data) с полями:
    - first_name (обязательно) - Имя пользователя
    - last_name (обязательно) - Фамилия пользователя
    - email (обязательно) - Email (должен быть валидным форматом)
    - password (обязательно) - Пароль (минимум 6 символов)
    - avatar (опционально) - Файл изображения для аватара
    
    Валидирует данные, проверяет уникальность email, сохраняет аватар если есть,
    хеширует пароль и создает пользователя в БД.
    
    Returns:
        JSON ответ с user_id (201) или ошибкой (400, 409)
    """
    data = RegisterSchema().load(request.form.to_dict())
    email = data["email"]
    first_name = data["first_name"]
    last_name = data["last_name"]
    password = data["password"]
    
    if User.query.filter_by(email=email).first():
        current_app.logger.warning(
            "user_register_conflict",
            extra={"event": "user_register_conflict", "email": email},
        )
        raise ConflictError("User already exists")

    user = User(first_name=first_name, last_name=last_name, email=email)
    user.set_password(password)

    if "avatar" in request.files:
        f = request.files["avatar"]
        saved = save_avatar(f)
        if saved is None:
            return jsonify({"msg":"Invalid avatar extension"}), 400
        user.avatar = saved

    db.session.add(user)
    db.session.commit()
    current_app.logger.info(
        "user_registered",
        extra={"event": "user_registered", "user_id": user.id, "email": user.email},
    )
    return jsonify({"msg":"User created", "user_id": user.id}), 201

@auth_bp.route("/login", methods=["POST"])
@limiter.limit(lambda: current_app.config["RATE_LIMIT_AUTH"])
def login():
    """
    Вход в систему (авторизация пользователя).
    
    Принимает JSON с полями:
    - email (обязательно) - Email пользователя
    - password (обязательно) - Пароль пользователя
    
    Валидирует email, проверяет существование пользователя и правильность пароля.
    Генерирует JWT токен для дальнейшей аутентификации.
    
    Returns:
        JSON ответ с access_token и данными пользователя (200) или ошибкой (400, 401)
    """
    data = LoginSchema().load(request.get_json() or {})
    email = data["email"]
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(data["password"]):
        current_app.logger.warning(
            "user_login_failed",
            extra={"event": "user_login_failed", "email": email},
        )
        raise UnauthorizedError("Bad email or password")
    access_token = create_access_token(identity=str(user.id))
    current_app.logger.info(
        "user_login_success",
        extra={"event": "user_login_success", "user_id": user.id, "email": user.email},
    )
    return jsonify({"access_token": access_token, "user": {
        "id": user.id, "first_name": user.first_name, "last_name": user.last_name,
        "email": user.email, "avatar": user.avatar
    }}), 200

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """
    Получение данных текущего пользователя (личный кабинет).
    
    Требует JWT токен в заголовке Authorization.
    Получает пользователя по ID из токена и возвращает его данные,
    включая количество непрочитанных уведомлений.
    
    Returns:
        JSON ответ с данными пользователя и unread_notifications (200) или ошибкой (401, 404)
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError("User not found")
    # количество непрочитанных уведомлений
    unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
    return jsonify({
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "avatar": user.avatar,
        "unread_notifications": unread_count
    }), 200

@auth_bp.route("/notifications", methods=["GET"])
@jwt_required()
def get_notifications():
    """
    Получение списка уведомлений пользователя.
    
    Требует JWT токен. Параметры запроса:
    - unread_only (опционально, "true"/"false") - Показывать только непрочитанные
    - limit (опционально, число) - Максимум уведомлений (по умолчанию 50)
    
    Фильтрует уведомления по пользователю, применяет фильтр по прочитанности,
    сортирует по дате (новые первые) и ограничивает количество.
    
    Returns:
        JSON массив уведомлений (200) или ошибка авторизации (401)
    """
    user_id = get_jwt_identity()
    # параметры: ?unread_only=true&limit=10
    unread_only = request.args.get("unread_only", type=str) == "true"
    limit = request.args.get("limit", type=int, default=50)
    
    query = Notification.query.filter_by(user_id=user_id)
    if unread_only:
        query = query.filter_by(is_read=False)
    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
    
    return jsonify([{
        "id": n.id,
        "title": n.title,
        "message": n.message,
        "type": n.type,
        "is_read": n.is_read,
        "created_at": n.created_at.isoformat()
    } for n in notifications]), 200

@auth_bp.route("/notifications/<int:notification_id>/read", methods=["PUT"])
@jwt_required()
def mark_notification_read(notification_id):
    """
    Отметить конкретное уведомление как прочитанное.
    
    Требует JWT токен. Проверяет что уведомление принадлежит текущему пользователю
    и помечает его как прочитанное (is_read = True).
    
    Args:
        notification_id (int): ID уведомления для отметки
        
    Returns:
        JSON ответ с подтверждением (200) или ошибкой (401, 404)
    """
    user_id = get_jwt_identity()
    notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if not notification:
        raise NotFoundError("Notification not found")
    notification.is_read = True
    db.session.commit()
    return jsonify({"msg":"Notification marked as read"}), 200

@auth_bp.route("/notifications/read-all", methods=["PUT"])
@jwt_required()
def mark_all_notifications_read():
    """
    Отметить все уведомления пользователя как прочитанные.
    
    Требует JWT токен. Обновляет все непрочитанные уведомления текущего пользователя,
    устанавливая is_read = True для всех записей.
    
    Returns:
        JSON ответ с подтверждением (200) или ошибка авторизации (401)
    """
    user_id = get_jwt_identity()
    Notification.query.filter_by(user_id=user_id, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"msg":"All notifications marked as read"}), 200

@auth_bp.route("/avatar/<filename>", methods=["GET"])
def avatar(filename):
    """
    Получение файла аватара пользователя.
    
    Отдает файл изображения аватара из папки static/avatars.
    Используется если фронтенд не может напрямую обращаться к статическим файлам.
    
    Args:
        filename (str): Имя файла аватара
        
    Returns:
        Файл изображения или ошибка 404 если файл не найден
    """
    folder = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(folder, filename)