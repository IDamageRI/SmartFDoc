import sqlite3
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.config import DATABASE_PATH

def apply_migration(db_path=None):
    """Добавляет поле sender_email в таблицу external_documents"""
    if db_path is None:
        db_path = DATABASE_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(external_documents)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'sender_email' not in columns:
            cursor.execute("""
                ALTER TABLE external_documents 
                ADD COLUMN sender_email TEXT
            """)
            print("✓ Добавлено поле sender_email")
        else:
            print("✓ Поле sender_email уже существует")
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_external_docs_sender_email 
            ON external_documents(sender_email)
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

