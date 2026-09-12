"""
Сервис управления файлами
"""
import os
from pathlib import Path
from datetime import datetime
from backend.config import STORAGE_INTERNAL, STORAGE_EXTERNAL


def generate_file_path(category, department_name, year, document_type, document_date=None, expiry_date=None, filename=None):
    """
    Генерирует путь к файлу согласно структуре:
    storage/{category}/{department}/{year}/{document_type}/{document_date}/{expiry_date}/{filename}
    
    Args:
        category: 'internal' или 'external'
        department_name: Название отдела
        year: Год
        document_type: Тип документа
        document_date: Дата документа (опционально)
        expiry_date: Срок исполнения (опционально)
        filename: Имя файла
        
    Returns:
        Path: Путь к файлу
    """
    # Нормализуем названия для файловой системы
    def sanitize(name):
        """Очищает имя для использования в пути файловой системы"""
        if not name:
            return ""
        # Заменяем недопустимые символы
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name.strip()
    
    # Определяем базовую директорию
    if category == 'internal':
        base_dir = STORAGE_INTERNAL
    else:
        base_dir = STORAGE_EXTERNAL
    
    # Строим путь
    path_parts = [
        sanitize(department_name),
        str(year),
        sanitize(document_type)
    ]
    
    if document_date:
        # Форматируем дату как YYYY-MM-DD
        if isinstance(document_date, str):
            date_str = document_date[:10]  # Берем только дату
        else:
            date_str = document_date.strftime('%Y-%m-%d')
        path_parts.append(date_str)
    
    if expiry_date:
        if isinstance(expiry_date, str):
            expiry_str = expiry_date[:10]
        else:
            expiry_str = expiry_date.strftime('%Y-%m-%d')
        path_parts.append(f"expiry_{expiry_str}")
    
    # Создаем полный путь
    file_path = base_dir
    for part in path_parts:
        if part:
            file_path = file_path / part
    
    # Создаем директории если их нет
    file_path.mkdir(parents=True, exist_ok=True)
    
    # Добавляем имя файла если указано
    if filename:
        file_path = file_path / filename
    
    return file_path


def save_file(file, file_path):
    """
    Сохраняет файл по указанному пути
    
    Args:
        file: Файл из request.files
        file_path: Path объект для сохранения
        
    Returns:
        bool: True если успешно
    """
    try:
        file.save(str(file_path))
        return True
    except Exception as e:
        print(f"Ошибка сохранения файла: {e}")
        return False


def get_file_extension(filename):
    """Получает расширение файла"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''


def get_file_size(file_path):
    """Получает размер файла в байтах"""
    try:
        return os.path.getsize(file_path)
    except:
        return 0

