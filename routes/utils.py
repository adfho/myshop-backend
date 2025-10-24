import os
from flask import current_app
from werkzeug.utils import secure_filename
from uuid import uuid4

def allowed_file(filename):
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config['ALLOWED_EXTENSIONS']

def save_avatar(file_storage):
    # file_storage = request.files['avatar']
    if not allowed_file(file_storage.filename):
        return None
    filename = secure_filename(file_storage.filename)
    unique = f"{uuid4().hex}_{filename}"
    path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique)
    file_storage.save(path)
    # вернём относительный путь для сохранения в БД
    return os.path.join("static", "avatars", unique)