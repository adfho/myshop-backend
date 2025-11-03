"""
Скрипт для заполнения базы данных тестовыми данными.

⚠️ ВНИМАНИЕ: Этот скрипт УДАЛЯЕТ все данные из БД (db.drop_all)!
Используйте только для разработки и тестирования, НЕ запускайте на production!

Выполняет следующие действия:
1. Удаляет все существующие таблицы из БД (db.drop_all)
2. Создает все таблицы заново (db.create_all)
3. Создает тестовые категории товаров (Electronics, Books)
4. Создает тестовые товары с ценами и остатками на складе
5. Создает тестового пользователя для проверки функционала

Запуск: python data_seed.py
После выполнения выводит "Seed done" в консоль.
"""

import sys
from app import create_app
from models import db, Category, Product, User

app = create_app()

# Проверяем окружение - в проде запрещаем запуск
with app.app_context():
    env = app.config.get('ENV', 'development')
    if env == 'production':
        print("❌ ОШИБКА: Нельзя запускать data_seed.py в production окружении!")
        print("Этот скрипт удаляет все данные из БД (db.drop_all)!")
        sys.exit(1)

# Предупреждение для пользователя
print("⚠️  ВНИМАНИЕ: Этот скрипт удалит все данные из базы данных!")
response = input("Вы уверены? Введите 'yes' для продолжения: ")
if response.lower() != 'yes':
    print("Отменено.")
    sys.exit(0)

with app.app_context():
    db.drop_all()
    db.create_all()
    # категории
    cat1 = Category(name="Electronics")
    cat2 = Category(name="Books")
    db.session.add_all([cat1, cat2])
    db.session.commit()
    # товары (используем Decimal для цен)
    from decimal import Decimal
    p1 = Product(
        title="Smartphone", description="Good phone",
        price=Decimal("299.99"), stock=10, category_id=cat1.id
    )
    p2 = Product(
        title="Laptop", description="Work laptop",
        price=Decimal("899.00"), stock=5, category_id=cat1.id
    )
    p3 = Product(
        title="Python Book", description="Learn Python",
        price=Decimal("29.00"), stock=50, category_id=cat2.id
    )
    db.session.add_all([p1,p2,p3])
    # тестовый пользователь
    u = User(first_name="Test", last_name="User", email="test@example.com")
    u.set_password("password")
    db.session.add(u)
    db.session.commit()
    print("Seed done")
    