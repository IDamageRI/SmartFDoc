"""
Скрипт для добавления поля expiry_date в таблицы документов
"""
import sqlite3
from pathlib import Path


def add_expiry_date(db_path: str = "documents.db"):
    """Добавляет поле expiry_date в таблицы документов"""
    script_dir = Path(__file__).parent
    db_full_path = script_dir / db_path
    
    if not db_full_path.exists():
        print(f"База данных не найдена: {db_full_path}")
        return
    
    conn = sqlite3.connect(db_full_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    
    try:
        # Добавляем поле в internal_documents
        try:
            cursor.execute("ALTER TABLE internal_documents ADD COLUMN expiry_date DATE")
            print("✓ Поле expiry_date добавлено в internal_documents")
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                raise
            print("✓ Поле expiry_date уже существует в internal_documents")
        
        # Добавляем поле в external_documents
        try:
            cursor.execute("ALTER TABLE external_documents ADD COLUMN expiry_date DATE")
            print("✓ Поле expiry_date добавлено в external_documents")
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                raise
            print("✓ Поле expiry_date уже существует в external_documents")
        
        conn.commit()
        print("\n✓ Миграция выполнена успешно")
        
    except sqlite3.Error as e:
        print(f"❌ Ошибка: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    add_expiry_date()

