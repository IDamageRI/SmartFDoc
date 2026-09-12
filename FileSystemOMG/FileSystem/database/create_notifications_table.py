"""
Скрипт для создания таблицы уведомлений
"""
import sqlite3
from pathlib import Path


def create_notifications_table(db_path: str = "documents.db"):
    """Создает таблицу уведомлений"""
    script_dir = Path(__file__).parent
    db_full_path = script_dir / db_path
    
    if not db_full_path.exists():
        print(f"База данных не найдена: {db_full_path}")
        return
    
    conn = sqlite3.connect(db_full_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    
    try:
        # Создаем таблицу
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT,
                document_id INTEGER,
                document_table TEXT,
                is_read BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Создаем индексы
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_notifications_user 
            ON notifications(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_notifications_read 
            ON notifications(user_id, is_read)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_notifications_created 
            ON notifications(created_at DESC)
        """)
        
        conn.commit()
        print("✓ Таблица notifications создана")
        print("✓ Индексы созданы")
        
    except sqlite3.Error as e:
        print(f"❌ Ошибка: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    create_notifications_table()

