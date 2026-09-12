"""
Скрипт для добавления пользователей в базу данных
"""
import sqlite3
from pathlib import Path


def get_db_connection(db_path: str = "documents.db"):
    """Создает подключение к базе данных"""
    script_dir = Path(__file__).parent
    db_full_path = script_dir / db_path
    
    if not db_full_path.exists():
        raise FileNotFoundError(f"База данных не найдена: {db_full_path}")
    
    conn = sqlite3.connect(db_full_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def add_departments_if_needed(cursor):
    """Добавляет отделы, если их еще нет"""
    cursor.execute("SELECT COUNT(*) FROM departments")
    if cursor.fetchone()[0] == 0:
        departments = [
            ("IT-отдел", "Отдел информационных технологий"),
            ("Отдел закупок", "Отдел закупок и снабжения"),
            ("Бухгалтерия", "Финансовый отдел"),
            ("Отдел кадров", "Управление персоналом"),
            ("Юридический отдел", "Правовое обеспечение"),
            ("Руководство", "Руководящий состав компании"),
        ]
        cursor.executemany(
            "INSERT INTO departments (name, description) VALUES (?, ?)",
            departments
        )
        print("✓ Добавлены отделы")
        return True
    return False


def add_users(cursor):
    """Добавляет пользователей с разными ролями"""
    
    # Получаем ID отделов
    cursor.execute("SELECT id, name FROM departments")
    depts = {name: id for id, name in cursor.fetchall()}
    
    users = [
        # Администратор - все права
        {
            "username": "admin",
            "full_name": "Администратор Системы",
            "email": "admin@company.com",
            "department_id": depts.get("Руководство"),
            "role": "admin"
        },
        
        # Руководители отделов - могут просматривать все документы своего отдела
        {
            "username": "director_it",
            "full_name": "Иванов Иван Иванович",
            "email": "ivanov@company.com",
            "department_id": depts.get("IT-отдел"),
            "role": "manager"
        },
        {
            "username": "director_procurement",
            "full_name": "Петрова Мария Сергеевна",
            "email": "petrova@company.com",
            "department_id": depts.get("Отдел закупок"),
            "role": "manager"
        },
        {
            "username": "director_hr",
            "full_name": "Сидоров Петр Александрович",
            "email": "sidorov@company.com",
            "department_id": depts.get("Отдел кадров"),
            "role": "manager"
        },
        
        # Обычные сотрудники - могут просматривать документы своего отдела и созданные лично
        {
            "username": "employee_procurement_1",
            "full_name": "Козлова Анна Викторовна",
            "email": "kozlova@company.com",
            "department_id": depts.get("Отдел закупок"),
            "role": "user"
        },
        {
            "username": "employee_procurement_2",
            "full_name": "Морозов Дмитрий Игоревич",
            "email": "morozov@company.com",
            "department_id": depts.get("Отдел закупок"),
            "role": "user"
        },
        {
            "username": "employee_it_1",
            "full_name": "Волков Алексей Николаевич",
            "email": "volkov@company.com",
            "department_id": depts.get("IT-отдел"),
            "role": "user"
        },
        {
            "username": "employee_it_2",
            "full_name": "Новикова Елена Дмитриевна",
            "email": "novikova@company.com",
            "department_id": depts.get("IT-отдел"),
            "role": "user"
        },
        {
            "username": "employee_accounting",
            "full_name": "Лебедева Ольга Сергеевна",
            "email": "lebedeva@company.com",
            "department_id": depts.get("Бухгалтерия"),
            "role": "user"
        },
    ]
    
    added_count = 0
    skipped_count = 0
    
    for user in users:
        try:
            cursor.execute(
                """INSERT INTO users (username, full_name, email, department_id, role) 
                   VALUES (?, ?, ?, ?, ?)""",
                (user["username"], user["full_name"], user["email"], 
                 user["department_id"], user["role"])
            )
            added_count += 1
        except sqlite3.IntegrityError:
            # Пользователь уже существует
            skipped_count += 1
    
    return added_count, skipped_count


def main():
    """Основная функция"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("=== Добавление пользователей ===\n")
        
        # Добавляем отделы, если нужно
        add_departments_if_needed(cursor)
        
        # Добавляем пользователей
        print("\nДобавление пользователей...")
        added, skipped = add_users(cursor)
        
        # Сохраняем изменения
        conn.commit()
        
        print(f"\n✓ Добавлено новых пользователей: {added}")
        if skipped > 0:
            print(f"  Пропущено (уже существуют): {skipped}")
        
        # Выводим список всех пользователей
        print("\n📋 Список пользователей:")
        cursor.execute("""
            SELECT u.id, u.username, u.full_name, u.role, d.name as department
            FROM users u
            LEFT JOIN departments d ON u.department_id = d.id
            ORDER BY u.role, u.username
        """)
        
        users = cursor.fetchall()
        current_role = None
        for user in users:
            role = user[3]
            if role != current_role:
                current_role = role
                role_name = {
                    "admin": "👑 АДМИНИСТРАТОРЫ",
                    "manager": "👔 РУКОВОДИТЕЛИ ОТДЕЛОВ",
                    "user": "👤 ОБЫЧНЫЕ СОТРУДНИКИ"
                }.get(role, role.upper())
                print(f"\n{role_name}:")
            
            dept = user[4] if user[4] else "Без отдела"
            print(f"  [{user[0]}] {user[1]} ({user[2]}) - {dept}")
        
        # Статистика по ролям
        print("\n📊 Статистика:")
        cursor.execute("""
            SELECT role, COUNT(*) as count 
            FROM users 
            GROUP BY role
        """)
        stats = cursor.fetchall()
        for role, count in stats:
            role_name = {
                "admin": "Администраторы",
                "manager": "Руководители отделов",
                "user": "Обычные сотрудники"
            }.get(role, role)
            print(f"  {role_name}: {count}")
        
    except sqlite3.Error as e:
        print(f"\n❌ Ошибка базы данных: {e}")
        conn.rollback()
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        conn.rollback()
    finally:
        conn.close()
        print("\n✓ Готово")


if __name__ == "__main__":
    main()

