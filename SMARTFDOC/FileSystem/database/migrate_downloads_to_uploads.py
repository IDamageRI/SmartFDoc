import sqlite3
from pathlib import Path
import sys

BASE_DIR = Path(__file__).parent.parent
DATABASE_PATH = BASE_DIR / "database" / "documents.db"

def migrate():
    if not DATABASE_PATH.exists():
        print(f"База данных не найдена: {DATABASE_PATH}")
        return
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='download_logs'")
        if cursor.fetchone():
            print("Переименование таблицы download_logs в upload_logs...")
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS upload_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    category TEXT NOT NULL CHECK(category IN ('internal', 'external')),
                    user_id INTEGER NOT NULL,
                    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            cursor.execute("""
                INSERT INTO upload_logs (document_id, category, user_id, uploaded_at)
                SELECT document_id, category, user_id, downloaded_at
                FROM download_logs
            """)
            
            cursor.execute("DROP TABLE download_logs")
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_upload_logs_document ON upload_logs(document_id, category)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_upload_logs_user ON upload_logs(user_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_upload_logs_date ON upload_logs(uploaded_at)
            """)
            
            conn.commit()
            print("Миграция успешно выполнена!")
        else:
            print("Таблица download_logs не найдена. Проверяю наличие upload_logs...")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='upload_logs'")
            if cursor.fetchone():
                print("Таблица upload_logs уже существует.")
            else:
                print("Создание таблицы upload_logs...")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS upload_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        document_id INTEGER NOT NULL,
                        category TEXT NOT NULL CHECK(category IN ('internal', 'external')),
                        user_id INTEGER NOT NULL,
                        uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_upload_logs_document ON upload_logs(document_id, category)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_upload_logs_user ON upload_logs(user_id)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_upload_logs_date ON upload_logs(uploaded_at)
                """)
                
                conn.commit()
                print("Таблица upload_logs создана!")
    
    except Exception as e:
        conn.rollback()
        print(f"Ошибка при миграции: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()

