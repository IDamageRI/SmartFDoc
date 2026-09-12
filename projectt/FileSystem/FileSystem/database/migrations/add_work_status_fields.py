"""
Миграция для добавления полей work_status и completion_percent
"""
import sqlite3
from pathlib import Path
import sys

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.config import DATABASE_PATH

def apply_migration():
    """Применяет миграцию"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Добавляем поля в internal_documents
        try:
            cursor.execute("ALTER TABLE internal_documents ADD COLUMN expiry_date DATE")
            print("[OK] Добавлено поле expiry_date в internal_documents")
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                print(f"  Поле expiry_date уже существует или ошибка: {e}")
        
        try:
            cursor.execute("ALTER TABLE internal_documents ADD COLUMN work_status TEXT DEFAULT 'not_processed'")
            print("[OK] Добавлено поле work_status в internal_documents")
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                print(f"  Поле work_status уже существует или ошибка: {e}")
        
        try:
            cursor.execute("ALTER TABLE internal_documents ADD COLUMN completion_percent INTEGER DEFAULT 0")
            print("[OK] Добавлено поле completion_percent в internal_documents")
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                print(f"  Поле completion_percent уже существует или ошибка: {e}")
        
        # Добавляем поля в external_documents
        try:
            cursor.execute("ALTER TABLE external_documents ADD COLUMN expiry_date DATE")
            print("[OK] Добавлено поле expiry_date в external_documents")
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                print(f"  Поле expiry_date уже существует или ошибка: {e}")
        
        try:
            cursor.execute("ALTER TABLE external_documents ADD COLUMN work_status TEXT DEFAULT 'not_processed'")
            print("[OK] Добавлено поле work_status в external_documents")
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                print(f"  Поле work_status уже существует или ошибка: {e}")
        
        try:
            cursor.execute("ALTER TABLE external_documents ADD COLUMN completion_percent INTEGER DEFAULT 0")
            print("[OK] Добавлено поле completion_percent в external_documents")
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                print(f"  Поле completion_percent уже существует или ошибка: {e}")
        
        conn.commit()
        print("\n[OK] Миграция успешно применена!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Ошибка применения миграции: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    apply_migration()

