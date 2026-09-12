import sqlite3
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.config import DATABASE_PATH

def apply_migration(db_path=None):
    """Добавляет поля sender_inn и sender_kpp в таблицу external_documents"""
    if db_path is None:
        db_path = DATABASE_PATH
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(external_documents)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'sender_inn' not in columns:
            cursor.execute("""
                ALTER TABLE external_documents 
                ADD COLUMN sender_inn TEXT
            """)
            print("✓ Добавлено поле sender_inn")
        else:
            print("✓ Поле sender_inn уже существует")
        
        if 'sender_kpp' not in columns:
            cursor.execute("""
                ALTER TABLE external_documents 
                ADD COLUMN sender_kpp TEXT
            """)
            print("✓ Добавлено поле sender_kpp")
        else:
            print("✓ Поле sender_kpp уже существует")
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_external_docs_sender_inn 
            ON external_documents(sender_inn)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_external_docs_sender_kpp 
            ON external_documents(sender_kpp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_external_docs_sender_name 
            ON external_documents(sender_name)
        """)
        
        conn.commit()
        print("✓ Миграция успешно применена")
        
    except Exception as e:
        print(f"❌ Ошибка при применении миграции: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    apply_migration()

