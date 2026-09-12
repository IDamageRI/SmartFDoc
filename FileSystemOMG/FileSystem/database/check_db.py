"""
Скрипт для проверки структуры базы данных
"""
import sqlite3
from pathlib import Path


def check_database(db_path: str = "documents.db"):
    """Проверяет структуру базы данных"""
    script_dir = Path(__file__).parent
    db_full_path = script_dir / db_path
    
    if not db_full_path.exists():
        print(f"База данных не найдена: {db_full_path}")
        return
    
    conn = sqlite3.connect(db_full_path)
    # Включаем внешние ключи для проверки
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    
    try:
        # Проверка внешних ключей
        cursor.execute("PRAGMA foreign_keys")
        fk_enabled = cursor.fetchone()[0]
        print(f"✓ Внешние ключи: {'включены' if fk_enabled else 'выключены'}")
        
        # Список таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
        tables = cursor.fetchall()
        print(f"\n✓ Таблицы ({len(tables)}):")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Индексы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
        indexes = cursor.fetchall()
        print(f"\n✓ Индексы ({len(indexes)}):")
        for idx in indexes:
            print(f"  - {idx[0]}")
        
        # Триггеры
        cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
        triggers = cursor.fetchall()
        print(f"\n✓ Триггеры ({len(triggers)}):")
        for trigger in triggers:
            print(f"  - {trigger[0]}")
        
        print("\n✓ База данных структурирована корректно")
        
    except sqlite3.Error as e:
        print(f"✗ Ошибка при проверке: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else "documents.db"
    check_database(db_path)

