"""
Скрипт для заполнения базы данных тестовыми данными (опционально)
"""
import sqlite3
from pathlib import Path


def seed_database(db_path: str = "documents.db"):
    """
    Заполняет базу данных тестовыми данными для разработки
    
    Args:
        db_path: Путь к файлу базы данных
    """
    script_dir = Path(__file__).parent
    db_full_path = script_dir / db_path
    
    if not db_full_path.exists():
        print(f"База данных не найдена: {db_full_path}")
        print("Сначала запустите init_db.py")
        return
    
    conn = sqlite3.connect(db_full_path)
    cursor = conn.cursor()
    
    try:
        # Добавляем тестовые отделы
        departments = [
            ("Отдел кадров", "Управление персоналом"),
            ("Бухгалтерия", "Финансовый отдел"),
            ("IT-отдел", "Информационные технологии"),
            ("Юридический отдел", "Правовое обеспечение"),
        ]
        
        cursor.executemany(
            "INSERT OR IGNORE INTO departments (name, description) VALUES (?, ?)",
            departments
        )
        
        # Добавляем типы документов
        document_types = [
            ("Приказ", "Распорядительный документ", "internal"),
            ("Заявление", "Обращение сотрудника", "internal"),
            ("Договор", "Соглашение между сторонами", None),
            ("Счет", "Финансовый документ", "external"),
            ("Письмо", "Корреспонденция", "external"),
            ("Акт", "Документ о выполнении работ", None),
        ]
        
        cursor.executemany(
            "INSERT OR IGNORE INTO document_types (name, description, category) VALUES (?, ?, ?)",
            document_types
        )
        
        # Добавляем тестовых пользователей
        users = [
            ("admin", "Администратор Системы", "admin@company.com", 3, "admin"),
            ("ivanov", "Иванов Иван Иванович", "ivanov@company.com", 1, "user"),
            ("petrov", "Петров Петр Петрович", "petrov@company.com", 2, "user"),
            ("sidorov", "Сидоров Сидор Сидорович", "sidorov@company.com", 3, "manager"),
        ]
        
        cursor.executemany(
            """INSERT OR IGNORE INTO users (username, full_name, email, department_id, role) 
               VALUES (?, ?, ?, ?, ?)""",
            users
        )
        
        conn.commit()
        print("Тестовые данные успешно добавлены")
        
        # Выводим статистику
        cursor.execute("SELECT COUNT(*) FROM departments")
        dept_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM document_types")
        type_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        print(f"\nСтатистика:")
        print(f"  Отделов: {dept_count}")
        print(f"  Типов документов: {type_count}")
        print(f"  Пользователей: {user_count}")
        
    except sqlite3.Error as e:
        print(f"Ошибка при заполнении базы данных: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    
    db_path = sys.argv[1] if len(sys.argv) > 1 else "documents.db"
    
    try:
        seed_database(db_path)
    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)


