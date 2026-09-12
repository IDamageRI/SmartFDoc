import os
from werkzeug.security import generate_password_hash, check_password_hash
from backend.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE


def validate_file(file):
    if not file or not file.filename:
        return False, "Файл не выбран"
    
    filename = file.filename
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Недопустимое расширение файла. Разрешенные: {', '.join(ALLOWED_EXTENSIONS)}"
    
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Возвращаем указатель в начало
    
    if file_size > MAX_FILE_SIZE:
        return False, f"Файл слишком большой. Максимальный размер: {MAX_FILE_SIZE / 1024 / 1024} МБ"
    
    if file_size == 0:
        return False, "Файл пустой"
    
    return True, None


def hash_password(password):
    return generate_password_hash(password)


def check_password(password_hash, password):
    if not password_hash:
        return False
    return check_password_hash(password_hash, password)

