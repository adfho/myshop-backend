import os
import re
from flask import current_app, jsonify
from werkzeug.utils import secure_filename
from uuid import uuid4

def allowed_file(filename):
    """
    Проверяет разрешен ли формат файла для загрузки.
    
    Проверяет расширение файла на соответствие списку разрешенных
    форматов из конфига (ALLOWED_EXTENSIONS: png, jpg, jpeg).
    
    Args:
        filename (str): Имя файла с расширением
        
    Returns:
        bool: True если формат разрешен, False если нет
    """
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config['ALLOWED_EXTENSIONS']

def save_avatar(file_storage):
    """
    Сохраняет файл аватара на диск.
    
    Проверяет формат файла, безопасно обрабатывает имя файла (secure_filename),
    генерирует уникальное имя файла с помощью UUID, сохраняет в папку UPLOAD_FOLDER,
    возвращает относительный путь для сохранения в БД.
    
    Args:
        file_storage: Файловый объект из request.files['avatar']
        
    Returns:
        str: Относительный путь к сохраненному файлу (static/avatars/filename)
        или None если формат файла не поддерживается
    """
    # file_storage = request.files['avatar']
    if not allowed_file(file_storage.filename):
        return None
    filename = secure_filename(file_storage.filename)
    unique = f"{uuid4().hex}_{filename}"
    path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique)
    file_storage.save(path)
    # вернём относительный путь для сохранения в БД
    return os.path.join("static", "avatars", unique)

def validate_email(email):
    """
    Проверяет валидность формата email адреса.
    
    Использует регулярное выражение для проверки соответствия стандартному
    формату email (например, user@example.com).
    
    Args:
        email (str): Email адрес для проверки
        
    Returns:
        bool: True если формат валиден, False если нет или email пустой
    """
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_password(password):
    """
    Проверяет минимальную длину пароля.
    
    Проверяет что пароль содержит не менее 6 символов.
    
    Args:
        password (str): Пароль для проверки
        
    Returns:
        bool: True если пароль валиден (>= 6 символов), False если нет или пустой
    """
    if not password:
        return False
    return len(password) >= 6

def validate_positive_number(value, field_name="value"):
    """
    Проверяет что значение является положительным числом.
    
    Преобразует значение в float и проверяет что оно больше 0.
    
    Args:
        value: Значение для проверки
        field_name (str): Название поля (для сообщения об ошибке)
        
    Returns:
        tuple: (True, None) если валидно, (False, error_message) если нет
    """
    try:
        num = float(value)
        return num > 0, None
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid positive number"

def validate_integer(value, field_name="value", min_value=None):
    """
    Проверяет что значение является целым числом и соответствует ограничениям.
    
    Преобразует значение в int и проверяет минимальное значение если указано.
    
    Args:
        value: Значение для проверки
        field_name (str): Название поля (для сообщения об ошибке)
        min_value (int, optional): Минимальное допустимое значение
        
    Returns:
        tuple: (True, int_value) если валидно, (False, error_message) если нет
    """
    try:
        num = int(value)
        if min_value is not None and num < min_value:
            return False, f"{field_name} must be at least {min_value}"
        return True, num
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid integer"