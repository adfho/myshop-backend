"""
Скрипт для заполнения базы данных тестовыми данными.

Выполняет следующие действия:
1. Удаляет все существующие таблицы из БД (db.drop_all)
2. Создает все таблицы заново (db.create_all)
3. Создает тестовые категории товаров (Electronics, Books)
4. Создает тестовые товары с ценами и остатками на складе
5. Создает тестового пользователя для проверки функционала

Запуск: python data_seed.py
После выполнения выводит "Seed done" в консоль.
"""

from app import create_app
from models import db, Category, Product, User

app = create_app()
with app.app_context():
    db.drop_all()
    db.create_all()
    # категории
    cat1 = Category(name="Electronics")
    cat2 = Category(name="Books")
    db.session.add_all([cat1, cat2])
    db.session.commit()
    # товары
    p1 = Product(title="Smartphone", description="Good phone", price=299.99, stock=10, category_id=cat1.id)
    p2 = Product(title="Laptop", description="Work laptop", price=899.0, stock=5, category_id=cat1.id)
    p3 = Product(title="Python Book", description="Learn Python", price=29.0, stock=50, category_id=cat2.id)
    db.session.add_all([p1,p2,p3])
    # тестовый пользователь
    u = User(first_name="Test", last_name="User", email="test@example.com")
    u.set_password("password")
    db.session.add(u)
    db.session.commit()
    print("Seed done")
    