"""
Скрипт для обновления паролей пользователей
Добавляет поле password_hash и устанавливает временные пароли
"""
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash


def update_users_passwords(db_path: str = "documents.db", default_password: str = "123"):
    """
    Обновляет пароли пользователей
    
    Args:
        db_path: Путь к БД
        default_password: Пароль по умолчанию (в реальной системе должен быть уникальным)
    """
    script_dir = Path(__file__).parent
    db_full_path = script_dir / db_path
    
    if not db_full_path.exists():
        print(f"База данных не найдена: {db_full_path}")
        return
    
    conn = sqlite3.connect(db_full_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    
    try:
        # Добавляем поле password_hash если его нет
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
            print("✓ Поле password_hash добавлено")
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                raise
            print("✓ Поле password_hash уже существует")
        
        # Получаем всех пользователей без паролей
        cursor.execute("SELECT id, username FROM users WHERE password_hash IS NULL OR password_hash = ''")
        users = cursor.fetchall()
        
        if not users:
            print("✓ Все пользователи уже имеют пароли")
            return
        
        # Обновляем пароли
        password_hash = generate_password_hash(default_password)
        updated_count = 0
        
        for user_id, username in users:
            cursor.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (password_hash, user_id)
            )
            updated_count += 1
            print(f"  ✓ Пароль установлен для пользователя: {username}")
        
        conn.commit()
        print(f"\n✓ Обновлено паролей: {updated_count}")
        print(f"  Временный пароль для всех: {default_password}")
        print("  ⚠️ ВАЖНО: В продакшене каждый пользователь должен иметь уникальный пароль!")
        
    except sqlite3.Error as e:
        print(f"❌ Ошибка: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    update_users_passwords()

