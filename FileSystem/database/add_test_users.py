"""
Скрипт для добавления тестовых пользователей (manager и user)
"""
import sqlite3
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.utils.validators import hash_password

def get_db_connection():
    """Создает подключение к базе данных"""
    script_dir = Path(__file__).parent
    db_path = script_dir / "documents.db"
    
    if not db_path.exists():
        raise FileNotFoundError(f"База данных не найдена: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

def main():
    """Добавляет тестовых пользователей"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Получаем ID отдела IT-отдел
        cursor.execute("SELECT id FROM departments WHERE name = 'IT-отдел' LIMIT 1")
        it_dept = cursor.fetchone()
        it_dept_id = it_dept['id'] if it_dept else None
        
        # Получаем ID отдела Отдел закупок
        cursor.execute("SELECT id FROM departments WHERE name = 'Отдел закупок' LIMIT 1")
        proc_dept = cursor.fetchone()
        proc_dept_id = proc_dept['id'] if proc_dept else None
        
        # Пароль для всех тестовых пользователей
        password_hash = hash_password('123')
        
        test_users = [
            {
                'username': 'manager',
                'full_name': 'Тестовый Менеджер',
                'email': 'manager@test.com',
                'department_id': it_dept_id,
                'role': 'manager',
                'password_hash': password_hash
            },
            {
                'username': 'user',
                'full_name': 'Тестовый Пользователь',
                'email': 'user@test.com',
                'department_id': proc_dept_id,
                'role': 'user',
                'password_hash': password_hash
            }
        ]
        
        added = 0
        updated = 0
        
        for user in test_users:
            # Проверяем, существует ли пользователь
            cursor.execute("SELECT id FROM users WHERE username = ?", (user['username'],))
            existing = cursor.fetchone()
            
            if existing:
                # Обновляем существующего пользователя
                cursor.execute("""
                    UPDATE users 
                    SET full_name = ?, email = ?, department_id = ?, role = ?, password_hash = ?
                    WHERE username = ?
                """, (
                    user['full_name'],
                    user['email'],
                    user['department_id'],
                    user['role'],
                    user['password_hash'],
                    user['username']
                ))
                updated += 1
                print(f"[OK] Обновлен пользователь: {user['username']} ({user['role']})")
            else:
                # Добавляем нового пользователя
                cursor.execute("""
                    INSERT INTO users (username, full_name, email, department_id, role, password_hash)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user['username'],
                    user['full_name'],
                    user['email'],
                    user['department_id'],
                    user['role'],
                    user['password_hash']
                ))
                added += 1
                print(f"[OK] Добавлен пользователь: {user['username']} ({user['role']})")
        
        conn.commit()
        
        print(f"\nИтого:")
        print(f"  Добавлено: {added}")
        print(f"  Обновлено: {updated}")
        print(f"\nТестовые пользователи (пароль: 123):")
        print(f"  - manager (Менеджер IT-отдела)")
        print(f"  - user (Обычный сотрудник отдела закупок)")
        
    except Exception as e:
        print(f"[ERROR] Ошибка: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()

