"""
Утилиты для работы с базой данных
"""
import sqlite3
from pathlib import Path
from backend.config import DATABASE_PATH


def get_db_connection():
    """
    Создает и возвращает подключение к базе данных
    
    Returns:
        sqlite3.Connection: Подключение к БД
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row  # Возвращает строки как словари
    return conn


def init_db():
    """
    Инициализирует базу данных (создает таблицы если их нет)
    """
    schema_path = Path(__file__).parent.parent.parent / "database" / "schema.sql"
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Схема БД не найдена: {schema_path}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        cursor.executescript(schema_sql)
        
        # Добавляем поле password_hash если его нет
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
        except sqlite3.OperationalError:
            # Поле уже существует
            pass
        
        conn.commit()
    finally:
        conn.close()

