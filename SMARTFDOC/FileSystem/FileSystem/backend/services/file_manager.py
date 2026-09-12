import os
from pathlib import Path
from datetime import datetime
from backend.config import STORAGE_INTERNAL, STORAGE_EXTERNAL


def generate_file_path(category, department_name, year, document_type, document_date=None, expiry_date=None, filename=None):
    def sanitize(name):
        if not name:
            return ""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name.strip()

    def sanitize_filename(name):
        if not name:
            return ""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name.strip()
    
    if category == 'internal':
        base_dir = STORAGE_INTERNAL
    else:
        base_dir = STORAGE_EXTERNAL
    
    path_parts = [
        sanitize(department_name),
        str(year),
        sanitize(document_type)
    ]
    
    if document_date:
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
    
    file_path = base_dir
    for part in path_parts:
        if part:
            file_path = file_path / part
    
    if filename:
        filename = sanitize_filename(filename)
        file_path = file_path / filename
    
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    return file_path


def save_file(file, file_path):
    try:
        file.save(str(file_path))
        return True
    except Exception as e:
        print(f"Ошибка сохранения файла: {e}")
        return False


def get_file_extension(filename):
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''


def get_file_size(file_path):
    try:
        return os.path.getsize(file_path)
    except:
        return 0

