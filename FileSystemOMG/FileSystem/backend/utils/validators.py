"""
Валидация данных
"""
import os
from werkzeug.security import generate_password_hash, check_password_hash
from backend.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE


def validate_file(file):
    """
    Валидирует загружаемый файл
    
    Args:
        file: Файл из request.files
        
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    if not file or not file.filename:
        return False, "Файл не выбран"
    
    # Проверка расширения
    filename = file.filename
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Недопустимое расширение файла. Разрешенные: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # Проверка размера
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Возвращаем указатель в начало
    
    if file_size > MAX_FILE_SIZE:
        return False, f"Файл слишком большой. Максимальный размер: {MAX_FILE_SIZE / 1024 / 1024} МБ"
    
    if file_size == 0:
        return False, "Файл пустой"
    
    return True, None


def hash_password(password):
    """
    Хеширует пароль
    
    Args:
        password: Пароль в открытом виде
        
    Returns:
        str: Хешированный пароль
    """
    return generate_password_hash(password)


def check_password(password_hash, password):
    """
    Проверяет пароль
    
    Args:
        password_hash: Хешированный пароль из БД
        password: Пароль в открытом виде
        
    Returns:
        bool: True если пароль верный
    """
    if not password_hash:
        return False
    return check_password_hash(password_hash, password)

