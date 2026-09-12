"""
Скрипт для инициализации базы данных SQLite
"""
import sqlite3
import os
from pathlib import Path


def init_database(db_path: str = "documents.db"):
    """
    Инициализирует базу данных SQLite из файла schema.sql
    
    Args:
        db_path: Путь к файлу базы данных
    """
    # Получаем путь к директории со скриптом
    script_dir = Path(__file__).parent
    schema_path = script_dir / "schema.sql"
    db_full_path = script_dir / db_path
    
    # Проверяем существование файла схемы
    if not schema_path.exists():
        raise FileNotFoundError(f"Файл схемы не найден: {schema_path}")
    
    # Удаляем существующую БД, если нужно пересоздать
    if db_full_path.exists():
        print(f"База данных уже существует: {db_full_path}")
        response = input("Пересоздать базу данных? (y/n): ")
        if response.lower() == 'y':
            db_full_path.unlink()
            print("Старая база данных удалена")
        else:
            print("Инициализация отменена")
            return
    
    # Читаем SQL схему
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    # Создаем подключение к БД
    conn = sqlite3.connect(db_full_path)
    # Включаем поддержку внешних ключей
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    
    try:
        # Выполняем SQL скрипт
        cursor.executescript(schema_sql)
        conn.commit()
        print(f"База данных успешно создана: {db_full_path}")
        print("Все таблицы и индексы созданы")
        
        # Выводим информацию о созданных таблицах
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"\nСозданные таблицы ({len(tables)}):")
        for table in tables:
            print(f"  - {table[0]}")
        
    except sqlite3.Error as e:
        print(f"Ошибка при создании базы данных: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    
    # Можно указать путь к БД как аргумент командной строки
    db_path = sys.argv[1] if len(sys.argv) > 1 else "documents.db"
    
    try:
        init_database(db_path)
    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)


