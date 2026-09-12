"""
Пример использования базы данных
Демонстрирует базовые операции: подключение, добавление данных, выборка
"""
import sqlite3
from pathlib import Path
from datetime import date


def get_db_connection(db_path: str = "documents.db"):
    """
    Создает и возвращает подключение к базе данных
    
    Args:
        db_path: Путь к файлу базы данных
        
    Returns:
        sqlite3.Connection: Подключение к БД
    """
    script_dir = Path(__file__).parent
    db_full_path = script_dir / db_path
    
    conn = sqlite3.connect(db_full_path)
    # Включаем поддержку внешних ключей
    conn.execute("PRAGMA foreign_keys = ON")
    # Включаем возврат строк как словарей (опционально, для удобства)
    conn.row_factory = sqlite3.Row
    
    return conn


def example_usage():
    """Пример использования базы данных"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("=== Пример работы с базой данных ===\n")
        
        # 1. Добавляем отдел
        print("1. Добавление отдела...")
        cursor.execute(
            "INSERT INTO departments (name, description) VALUES (?, ?)",
            ("IT-отдел", "Отдел информационных технологий")
        )
        dept_id = cursor.lastrowid
        print(f"   ✓ Отдел создан с ID: {dept_id}")
        
        # 2. Добавляем тип документа
        print("\n2. Добавление типа документа...")
        cursor.execute(
            "INSERT INTO document_types (name, description, category) VALUES (?, ?, ?)",
            ("Приказ", "Распорядительный документ", "internal")
        )
        doc_type_id = cursor.lastrowid
        print(f"   ✓ Тип документа создан с ID: {doc_type_id}")
        
        # 3. Добавляем пользователя
        print("\n3. Добавление пользователя...")
        cursor.execute(
            """INSERT INTO users (username, full_name, email, department_id, role) 
               VALUES (?, ?, ?, ?, ?)""",
            ("admin", "Администратор Системы", "admin@company.com", dept_id, "admin")
        )
        user_id = cursor.lastrowid
        print(f"   ✓ Пользователь создан с ID: {user_id}")
        
        # 4. Добавляем внутренний документ
        print("\n4. Добавление внутреннего документа...")
        cursor.execute(
            """INSERT INTO internal_documents 
               (document_type_id, title, file_path, file_name, file_extension, 
                department_id, author_id, document_date) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                doc_type_id,
                "Приказ №1",
                "/documents/internal/2024/order_001.pdf",
                "order_001.pdf",
                "pdf",
                dept_id,
                user_id,
                date.today()
            )
        )
        doc_id = cursor.lastrowid
        print(f"   ✓ Документ создан с ID: {doc_id}")
        
        # Сохраняем изменения
        conn.commit()
        print("\n✓ Все изменения сохранены")
        
        # 5. Читаем данные
        print("\n5. Чтение данных из базы...")
        
        # Список отделов
        cursor.execute("SELECT id, name, description FROM departments")
        departments = cursor.fetchall()
        print(f"\n   Отделы ({len(departments)}):")
        for dept in departments:
            print(f"     - [{dept['id']}] {dept['name']}: {dept['description']}")
        
        # Список документов
        cursor.execute("""
            SELECT id, title, file_name, document_date 
            FROM internal_documents
        """)
        documents = cursor.fetchall()
        print(f"\n   Внутренние документы ({len(documents)}):")
        for doc in documents:
            print(f"     - [{doc['id']}] {doc['title']} ({doc['file_name']}) - {doc['document_date']}")
        
        # Сложный запрос с JOIN
        print("\n6. Запрос с объединением таблиц:")
        cursor.execute("""
            SELECT 
                d.title,
                dt.name as doc_type,
                dept.name as department,
                u.full_name as author,
                d.document_date
            FROM internal_documents d
            LEFT JOIN document_types dt ON d.document_type_id = dt.id
            LEFT JOIN departments dept ON d.department_id = dept.id
            LEFT JOIN users u ON d.author_id = u.id
        """)
        results = cursor.fetchall()
        for row in results:
            print(f"     - {row['title']} ({row['doc_type']}) | Отдел: {row['department']} | Автор: {row['author']}")
        
    except sqlite3.Error as e:
        print(f"\n❌ Ошибка базы данных: {e}")
        conn.rollback()
    finally:
        conn.close()
        print("\n✓ Подключение закрыто")


if __name__ == "__main__":
    example_usage()

