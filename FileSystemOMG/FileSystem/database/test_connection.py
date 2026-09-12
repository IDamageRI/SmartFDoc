"""
Простой скрипт для проверки подключения к базе данных
"""
import sqlite3
from pathlib import Path


def test_connection(db_path: str = "documents.db"):
    """Проверяет подключение к базе данных и выводит информацию"""
    script_dir = Path(__file__).parent
    db_full_path = script_dir / db_path
    
    if not db_full_path.exists():
        print(f"❌ База данных не найдена: {db_full_path}")
        return False
    
    try:
        # Подключаемся к БД
        conn = sqlite3.connect(db_full_path)
        # Включаем внешние ключи
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        print(f"✅ Успешное подключение к базе данных: {db_full_path}")
        print(f"   Размер файла: {db_full_path.stat().st_size} байт")
        
        # Проверяем версию SQLite
        cursor.execute("SELECT sqlite_version()")
        version = cursor.fetchone()[0]
        print(f"   Версия SQLite: {version}")
        
        # Проверяем количество записей в таблицах
        print("\n📊 Статистика по таблицам:")
        tables = ['departments', 'document_types', 'users', 'internal_documents', 'external_documents']
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   {table}: {count} записей")
            except sqlite3.Error as e:
                print(f"   {table}: ошибка - {e}")
        
        # Пример простого запроса
        print("\n📋 Пример запроса - список отделов:")
        cursor.execute("SELECT id, name FROM departments LIMIT 5")
        departments = cursor.fetchall()
        if departments:
            for dept in departments:
                print(f"   ID: {dept[0]}, Название: {dept[1]}")
        else:
            print("   (таблица пуста)")
        
        conn.close()
        print("\n✅ Подключение закрыто")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Ошибка подключения: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False


if __name__ == "__main__":
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else "documents.db"
    test_connection(db_path)

