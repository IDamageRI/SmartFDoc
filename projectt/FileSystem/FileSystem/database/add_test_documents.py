"""
Скрипт для добавления тестовых документов в БД и файловую систему
"""
import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import BASE_DIR, STORAGE_INTERNAL, STORAGE_EXTERNAL
from backend.services.file_manager import generate_file_path
from backend.utils.db import get_db_connection
from backend.models.department import Department
from backend.models.document_type import DocumentType
from backend.models.user import User


def create_test_file(file_path, content="Тестовый документ"):
    """Создает тестовый файл"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return file_path


def add_test_documents():
    """Добавляет тестовые документы"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Получаем данные из БД напрямую через cursor
        cursor.execute("SELECT * FROM departments LIMIT 1")
        dept_row = cursor.fetchone()
        if not dept_row:
            print("❌ Отделы не найдены. Сначала запустите:")
            print("   python database/seed_data.py")
            return
        
        cursor.execute("SELECT * FROM document_types LIMIT 1")
        type_row = cursor.fetchone()
        if not type_row:
            print("❌ Типы документов не найдены. Сначала запустите:")
            print("   python database/seed_data.py")
            return
        
        cursor.execute("SELECT * FROM users WHERE username = 'admin' LIMIT 1")
        user_row = cursor.fetchone()
        if not user_row:
            print("❌ Пользователь admin не найден. Сначала запустите:")
            print("   python database/add_users.py")
            return
        
        dept = Department.from_row(dept_row)
        doc_type = DocumentType.from_row(type_row)
        author = User.from_row(user_row)
        
        # Создаем тестовые документы
        test_docs = [
            {
                'title': 'Приказ №1 о назначении ответственного',
                'description': 'Тестовый приказ',
                'department': dept,
                'doc_type': doc_type,
                'year': 2024,
                'date': datetime.now().date(),
                'expiry_date': (datetime.now() + timedelta(days=30)).date(),
                'category': 'internal'
            },
            {
                'title': 'Договор поставки №123',
                'description': 'Договор с поставщиком',
                'department': dept,
                'doc_type': doc_type,
                'year': 2024,
                'date': (datetime.now() - timedelta(days=5)).date(),
                'expiry_date': (datetime.now() + timedelta(days=2)).date(),  # Скоро истечет
                'category': 'internal'
            },
            {
                'title': 'Счет на оплату №456',
                'description': 'Счет от поставщика',
                'department': dept,
                'doc_type': doc_type,
                'year': 2024,
                'date': (datetime.now() - timedelta(days=10)).date(),
                'expiry_date': None,
                'category': 'external',
                'sender_name': 'ООО "Поставщик"',
                'sender_contact': 'supplier@example.com'
            }
        ]
        
        added_count = 0
        
        for doc_data in test_docs:
            # Генерируем путь к файлу
            file_path = generate_file_path(
                category=doc_data['category'],
                department_name=doc_data['department'].name,
                year=doc_data['year'],
                document_type=doc_data['doc_type'].name if doc_data['doc_type'] else 'Документ',
                document_date=doc_data['date'].isoformat(),
                expiry_date=doc_data['expiry_date'].isoformat() if doc_data['expiry_date'] else None,
                filename=f"{doc_data['title'].replace(' ', '_')}.pdf"
            )
            
            # Создаем тестовый файл
            create_test_file(file_path, f"Содержимое документа: {doc_data['title']}")
            
            # Относительный путь от корня проекта
            relative_path = file_path.relative_to(BASE_DIR)
            file_size = file_path.stat().st_size
            file_ext = 'pdf'
            
            # Сохраняем в БД
            if doc_data['category'] == 'internal':
                cursor.execute("""
                    INSERT INTO internal_documents 
                    (document_type_id, title, description, file_path, file_name, 
                     file_size, file_extension, department_id, author_id, 
                     document_date, expiry_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc_data['doc_type'].id if doc_data['doc_type'] else None,
                    doc_data['title'],
                    doc_data['description'],
                    str(relative_path),
                    file_path.name,
                    file_size,
                    file_ext,
                    doc_data['department'].id,
                    author.id,
                    doc_data['date'].isoformat(),
                    doc_data['expiry_date'].isoformat() if doc_data['expiry_date'] else None
                ))
            else:
                cursor.execute("""
                    INSERT INTO external_documents 
                    (document_type_id, title, description, file_path, file_name, 
                     file_size, file_extension, sender_name, sender_contact,
                     recipient_department_id, document_date, received_date, expiry_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc_data['doc_type'].id if doc_data['doc_type'] else None,
                    doc_data['title'],
                    doc_data['description'],
                    str(relative_path),
                    file_path.name,
                    file_size,
                    file_ext,
                    doc_data.get('sender_name', ''),
                    doc_data.get('sender_contact', ''),
                    doc_data['department'].id,
                    doc_data['date'].isoformat(),
                    datetime.now().date().isoformat(),
                    doc_data['expiry_date'].isoformat() if doc_data['expiry_date'] else None
                ))
            
            added_count += 1
            print(f"✓ Создан документ: {doc_data['title']}")
            print(f"  Путь: {relative_path}")
        
        conn.commit()
        print(f"\n✓ Добавлено тестовых документов: {added_count}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    add_test_documents()

