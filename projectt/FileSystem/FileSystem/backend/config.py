"""
Конфигурация приложения
"""
import os
from pathlib import Path

# Базовый путь проекта
BASE_DIR = Path(__file__).parent.parent

# База данных
DATABASE_PATH = BASE_DIR / "database" / "documents.db"

# Хранилище файлов
STORAGE_PATH = BASE_DIR / "storage"
STORAGE_INTERNAL = STORAGE_PATH / "internal"
STORAGE_EXTERNAL = STORAGE_PATH / "external"

# Настройки Flask
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
SESSION_COOKIE_NAME = 'document_session'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'None'  # Для работы с CORS
SESSION_COOKIE_SECURE = False  # True для HTTPS

# Настройки загрузки файлов
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 МБ
ALLOWED_EXTENSIONS = {'doc', 'docx', 'pdf', 'rtf', 'txt', 'xlsx', 'jpg', 'jpeg'}

# Настройки уведомлений
EXPIRY_WARNING_DAYS = [3, 1]  # Предупреждения за 3 и 1 день до истечения

