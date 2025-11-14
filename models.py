from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    avatar = db.Column(db.String(300))  # путь к файлу в static/avatars
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    orders = db.relationship("Order", backref="user", lazy="selectin")
    notifications = db.relationship(
        "Notification", backref="user", lazy="selectin", cascade="all, delete-orphan"
    )

    def set_password(self, password):
        """
        Хеширует пароль и сохраняет его в password_hash.
        
        Args:
            password (str): Пароль пользователя для хеширования
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Проверяет соответствует ли переданный пароль сохраненному хешу.
        
        Args:
            password (str): Пароль для проверки
            
        Returns:
            bool: True если пароль верный, False если нет
        """
        return check_password_hash(self.password_hash, password)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    products = db.relationship(
        "Product",
        backref=db.backref("category", lazy="selectin"),
        lazy="selectin",
    )

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    # Используем Numeric(10, 2) вместо Float для точных денежных расчетов
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, default=0)
    image = db.Column(db.String(300))  # путь или URL
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=True, index=True)

class Order(db.Model):
    __table_args__ = (
        db.Index("ix_order_user_created_at", "user_id", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    # Используем Numeric(10, 2) вместо Float для точных денежных расчетов
    total = db.Column(db.Numeric(10, 2), nullable=False)
    items = db.relationship("OrderItem", backref="order", lazy="selectin")
    status = db.Column(db.String(50), default="created")  # created, paid, shipped, cancelled

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False)
    # Используем Numeric(10, 2) вместо Float для точных денежных расчетов
    price = db.Column(db.Numeric(10, 2), nullable=False)  # price at time of order
    product = db.relationship("Product", lazy="selectin")

class Notification(db.Model):
    __table_args__ = (
        db.Index("ix_notification_user_read", "user_id", "is_read"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default="info")  # info, success, warning, error
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)