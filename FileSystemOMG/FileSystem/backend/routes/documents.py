"""
Маршруты для работы с документами
"""
from flask import Blueprint, request, jsonify, send_file
from pathlib import Path
from datetime import datetime
from backend.models.document import Document
from backend.models.department import Department
from backend.models.document_type import DocumentType
from backend.utils.db import get_db_connection
from backend.utils.middleware import login_required
from backend.utils.validators import validate_file
from backend.services.permissions import can_view_document, can_edit_document, can_delete_document
from backend.services.file_manager import generate_file_path, save_file, get_file_extension, get_file_size
from backend.config import BASE_DIR

documents_bp = Blueprint('documents', __name__, url_prefix='/api/documents')


@documents_bp.route('', methods=['GET'])
@login_required
def get_documents(current_user):
    """Получает список документов с фильтрами"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Параметры фильтрации
        category = request.args.get('category', 'internal')  # internal или external
        department_id = request.args.get('department_id', type=int)
        type_id = request.args.get('type_id', type=int)
        author_id = request.args.get('author_id', type=int)
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        status = request.args.get('status', 'active')
        sort = request.args.get('sort', 'date_desc')
        
        # Определяем таблицу
        table_name = 'internal_documents' if category == 'internal' else 'external_documents'
        
        # Базовый запрос
        query = f"""
            SELECT d.*, 
                   dt.name as document_type_name,
                   dept.name as department_name,
                   u.full_name as author_name
            FROM {table_name} d
            LEFT JOIN document_types dt ON d.document_type_id = dt.id
            LEFT JOIN departments dept ON d.department_id = dept.id OR d.recipient_department_id = dept.id
            LEFT JOIN users u ON d.author_id = u.id
            WHERE d.status = ?
        """
        params = [status]
        
        # Фильтры по правам доступа
        # Внешние документы доступны всем
        if category == 'external':
            # Внешние документы доступны всем пользователям
            pass
        elif current_user.role == 'admin':
            # Администратор видит все
            pass
        elif current_user.role == 'manager':
            # Руководитель видит документы своего отдела
            query += " AND (d.department_id = ? OR d.recipient_department_id = ?)"
            params.extend([current_user.department_id, current_user.department_id])
        else:
            # Обычный сотрудник видит документы отдела + личные
            query += " AND (d.department_id = ? OR d.recipient_department_id = ? OR d.author_id = ? OR d.recipient_user_id = ?)"
            params.extend([
                current_user.department_id,
                current_user.department_id,
                current_user.id,
                current_user.id
            ])
        
        # Дополнительные фильтры
        if department_id:
            query += " AND (d.department_id = ? OR d.recipient_department_id = ?)"
            params.extend([department_id, department_id])
        
        if type_id:
            query += " AND d.document_type_id = ?"
            params.append(type_id)
        
        if author_id:
            query += " AND d.author_id = ?"
            params.append(author_id)
        
        if date_from:
            query += " AND d.document_date >= ?"
            params.append(date_from)
        
        if date_to:
            query += " AND d.document_date <= ?"
            params.append(date_to)
        
        # Сортировка (улучшенная с учетом NULL значений)
        if sort == 'date_desc':
            query += " ORDER BY COALESCE(d.document_date, d.created_at) DESC, d.created_at DESC"
        elif sort == 'date_asc':
            query += " ORDER BY COALESCE(d.document_date, d.created_at) ASC, d.created_at ASC"
        elif sort == 'title_asc':
            query += " ORDER BY d.title ASC, d.file_name ASC"
        elif sort == 'title_desc':
            query += " ORDER BY d.title DESC, d.file_name DESC"
        elif sort == 'type_asc':
            query += " ORDER BY dt.name ASC, d.title ASC"
        else:
            query += " ORDER BY d.created_at DESC, COALESCE(d.document_date, d.created_at) DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Преобразуем в словари
        documents = []
        for row in rows:
            doc = Document.from_row(row, table_name)
            doc_dict = doc.to_dict()
            doc_dict['category'] = category
            doc_dict['document_type_name'] = row['document_type_name'] if 'document_type_name' in row.keys() else None
            doc_dict['department_name'] = row['department_name'] if 'department_name' in row.keys() else None
            doc_dict['author_name'] = row['author_name'] if 'author_name' in row.keys() else None
            documents.append(doc_dict)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'documents': documents,
            'total': len(documents)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@documents_bp.route('/<int:doc_id>', methods=['GET'])
@login_required
def get_document(doc_id, current_user):
    """Получает детали документа"""
    try:
        category = request.args.get('category', 'internal')
        table_name = 'internal_documents' if category == 'internal' else 'external_documents'
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Загружаем документ с связанными данными
        sql = f"""
            SELECT d.*, 
                   dt.name as document_type_name,
                   dept.name as department_name,
                   u.full_name as author_name
            FROM {table_name} d
            LEFT JOIN document_types dt ON d.document_type_id = dt.id
            LEFT JOIN departments dept ON d.department_id = dept.id OR d.recipient_department_id = dept.id
            LEFT JOIN users u ON d.author_id = u.id
            WHERE d.id = ?
        """
        
        cursor.execute(sql, (doc_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({
                'success': False,
                'error': {'message': 'Документ не найден'}
            }), 404
        
        doc = Document.from_row(row, table_name)
        
        # Проверка прав доступа
        if not can_view_document(current_user, doc):
            return jsonify({
                'success': False,
                'error': {'message': 'Доступ запрещен'}
            }), 403
        
        doc_dict = doc.to_dict()
        doc_dict['category'] = category
        doc_dict['document_type_name'] = row['document_type_name'] if 'document_type_name' in row.keys() else None
        doc_dict['department_name'] = row['department_name'] if 'department_name' in row.keys() else None
        doc_dict['author_name'] = row['author_name'] if 'author_name' in row.keys() else None
        
        # Для внешних документов добавляем sender_name
        if category == 'external' and hasattr(doc, 'sender_name'):
            doc_dict['sender_name'] = doc.sender_name
        
        return jsonify({
            'success': True,
            'document': doc_dict
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@documents_bp.route('', methods=['POST'])
@login_required
def create_document(current_user):
    """Создает новый документ с загрузкой файла"""
    try:
        # Проверяем наличие файла
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': {'message': 'Файл не предоставлен'}
            }), 400
        
        file = request.files['file']
        
        # Валидация файла
        is_valid, error_msg = validate_file(file)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': {'message': error_msg}
            }), 400
        
        # Получаем метаданные
        category = request.form.get('category', 'internal')
        document_type_id = request.form.get('document_type_id', type=int)
        title = request.form.get('title', file.filename)
        description = request.form.get('description', '')
        department_id = request.form.get('department_id', type=int) or current_user.department_id
        recipient_department_id = request.form.get('recipient_department_id', type=int)
        recipient_user_id = request.form.get('recipient_user_id', type=int)
        document_date = request.form.get('document_date') or datetime.now().date().isoformat()
        expiry_date = request.form.get('expiry_date') or None
        
        # Получаем информацию об отделе и типе документа
        dept = Department.find_by_id(department_id)
        doc_type = DocumentType.find_by_id(document_type_id) if document_type_id else None
        
        # Генерируем путь к файлу
        year = datetime.now().year
        dept_name = dept.name if dept else f"department_{department_id}"
        type_name = doc_type.name if doc_type else "unknown"
        
        file_path = generate_file_path(
            category=category,
            department_name=dept_name,
            year=year,
            document_type=type_name,
            document_date=document_date,
            expiry_date=expiry_date,
            filename=file.filename
        )
        
        # Сохраняем файл
        if not save_file(file, file_path):
            return jsonify({
                'success': False,
                'error': {'message': 'Ошибка сохранения файла'}
            }), 500
        
        # Сохраняем в БД
        conn = get_db_connection()
        cursor = conn.cursor()
        
        file_size = get_file_size(file_path)
        file_ext = get_file_extension(file.filename)
        
        # Относительный путь от корня проекта
        relative_path = file_path.relative_to(BASE_DIR)
        
        if category == 'internal':
            cursor.execute("""
                INSERT INTO internal_documents 
                (document_type_id, title, description, file_path, file_name, 
                 file_size, file_extension, department_id, author_id, 
                 recipient_department_id, recipient_user_id, document_date, expiry_date,
                 work_status, completion_percent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                document_type_id, title, description, str(relative_path), file.filename,
                file_size, file_ext, department_id, current_user.id,
                recipient_department_id, recipient_user_id, document_date, expiry_date,
                'not_processed', 0
            ))
        else:
            sender_name = request.form.get('sender_name', '')
            sender_contact = request.form.get('sender_contact', '')
            received_date = request.form.get('received_date') or datetime.now().date().isoformat()
            
            cursor.execute("""
                INSERT INTO external_documents 
                (document_type_id, title, description, file_path, file_name, 
                 file_size, file_extension, sender_name, sender_contact,
                 recipient_department_id, recipient_user_id, document_date, received_date, expiry_date,
                 work_status, completion_percent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                document_type_id, title, description, str(relative_path), file.filename,
                file_size, file_ext, sender_name, sender_contact,
                recipient_department_id, recipient_user_id, document_date, received_date, expiry_date,
                'not_processed', 0
            ))
        
        doc_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Определяем имя таблицы для получения документа
        table_name = 'internal_documents' if category == 'internal' else 'external_documents'
        
        # Получаем созданный документ для уведомлений
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        conn.close()
        
        doc = Document.from_row(row, table_name)
        
        # Создаем уведомления
        from backend.services.notifications import create_document_notifications
        create_document_notifications(doc, table_name, current_user.id)
        
        return jsonify({
            'success': True,
            'document_id': doc_id,
            'message': 'Документ успешно загружен'
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@documents_bp.route('/<int:doc_id>', methods=['PUT'])
@login_required
def update_document(doc_id, current_user):
    """Обновляет метаданные документа"""
    try:
        category = request.json.get('category', 'internal')
        table_name = 'internal_documents' if category == 'internal' else 'external_documents'
        
        # Получаем документ
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return jsonify({
                'success': False,
                'error': {'message': 'Документ не найден'}
            }), 404
        
        doc = Document.from_row(row, table_name)
        
        # Проверка прав
        if not can_edit_document(current_user, doc):
            conn.close()
            return jsonify({
                'success': False,
                'error': {'message': 'Нет прав на редактирование'}
            }), 403
        
        # Обновляем поля
        data = request.json
        updates = []
        params = []
        
        # Общие поля для обеих таблиц
        if 'title' in data:
            updates.append("title = ?")
            params.append(data['title'].strip())
        
        if 'description' in data:
            updates.append("description = ?")
            params.append(data['description'].strip() if data['description'] else None)
        
        if 'document_type_id' in data:
            type_id = data['document_type_id']
            if type_id:
                # Проверяем существование типа документа
                cursor.execute("SELECT id FROM document_types WHERE id = ?", (type_id,))
                if not cursor.fetchone():
                    conn.close()
                    return jsonify({
                        'success': False,
                        'error': {'message': 'Тип документа не найден'}
                    }), 400
            updates.append("document_type_id = ?")
            params.append(type_id if type_id else None)
        
        if 'document_date' in data:
            updates.append("document_date = ?")
            params.append(data['document_date'] if data['document_date'] else None)
        
        if 'expiry_date' in data:
            updates.append("expiry_date = ?")
            params.append(data['expiry_date'] if data['expiry_date'] else None)
        
        if 'work_status' in data:
            updates.append("work_status = ?")
            params.append(data['work_status'])
        
        if 'completion_percent' in data:
            completion = data['completion_percent']
            if completion is not None:
                completion = max(0, min(100, int(completion)))  # Ограничиваем 0-100
            updates.append("completion_percent = ?")
            params.append(completion)
        
        # Поля для внутренних документов
        if table_name == 'internal_documents':
            if 'department_id' in data:
                dept_id = data['department_id']
                if dept_id:
                    cursor.execute("SELECT id FROM departments WHERE id = ?", (dept_id,))
                    if not cursor.fetchone():
                        conn.close()
                        return jsonify({
                            'success': False,
                            'error': {'message': 'Отдел не найден'}
                        }), 400
                updates.append("department_id = ?")
                params.append(dept_id if dept_id else None)
            
            if 'author_id' in data and current_user.role == 'admin':
                author_id = data['author_id']
                if author_id:
                    cursor.execute("SELECT id FROM users WHERE id = ?", (author_id,))
                    if not cursor.fetchone():
                        conn.close()
                        return jsonify({
                            'success': False,
                            'error': {'message': 'Автор не найден'}
                        }), 400
                updates.append("author_id = ?")
                params.append(author_id if author_id else None)
            
            if 'recipient_department_id' in data:
                rec_dept_id = data['recipient_department_id']
                if rec_dept_id:
                    cursor.execute("SELECT id FROM departments WHERE id = ?", (rec_dept_id,))
                    if not cursor.fetchone():
                        conn.close()
                        return jsonify({
                            'success': False,
                            'error': {'message': 'Отдел-получатель не найден'}
                        }), 400
                updates.append("recipient_department_id = ?")
                params.append(rec_dept_id if rec_dept_id else None)
            
            if 'recipient_user_id' in data:
                rec_user_id = data['recipient_user_id']
                if rec_user_id:
                    cursor.execute("SELECT id FROM users WHERE id = ?", (rec_user_id,))
                    if not cursor.fetchone():
                        conn.close()
                        return jsonify({
                            'success': False,
                            'error': {'message': 'Пользователь-получатель не найден'}
                        }), 400
                updates.append("recipient_user_id = ?")
                params.append(rec_user_id if rec_user_id else None)
        
        # Поля для внешних документов
        elif table_name == 'external_documents':
            if 'sender_name' in data:
                updates.append("sender_name = ?")
                params.append(data['sender_name'].strip() if data['sender_name'] else None)
            
            if 'sender_contact' in data:
                updates.append("sender_contact = ?")
                params.append(data['sender_contact'].strip() if data['sender_contact'] else None)
            
            if 'recipient_department_id' in data:
                rec_dept_id = data['recipient_department_id']
                if rec_dept_id:
                    cursor.execute("SELECT id FROM departments WHERE id = ?", (rec_dept_id,))
                    if not cursor.fetchone():
                        conn.close()
                        return jsonify({
                            'success': False,
                            'error': {'message': 'Отдел-получатель не найден'}
                        }), 400
                updates.append("recipient_department_id = ?")
                params.append(rec_dept_id if rec_dept_id else None)
            
            if 'recipient_user_id' in data:
                rec_user_id = data['recipient_user_id']
                if rec_user_id:
                    cursor.execute("SELECT id FROM users WHERE id = ?", (rec_user_id,))
                    if not cursor.fetchone():
                        conn.close()
                        return jsonify({
                            'success': False,
                            'error': {'message': 'Пользователь-получатель не найден'}
                        }), 400
                updates.append("recipient_user_id = ?")
                params.append(rec_user_id if rec_user_id else None)
            
            if 'received_date' in data:
                updates.append("received_date = ?")
                params.append(data['received_date'] if data['received_date'] else None)
        
        if 'status' in data:
            updates.append("status = ?")
            params.append(data['status'])
        
        if not updates:
            conn.close()
            return jsonify({
                'success': False,
                'error': {'message': 'Нет данных для обновления'}
            }), 400
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(doc_id)
        
        query = f"UPDATE {table_name} SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Документ обновлен'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@documents_bp.route('/<int:doc_id>', methods=['DELETE'])
@login_required
def delete_document(doc_id, current_user):
    """Удаляет документ (soft delete)"""
    try:
        category = request.args.get('category', 'internal')
        table_name = 'internal_documents' if category == 'internal' else 'external_documents'
        
        # Получаем документ
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return jsonify({
                'success': False,
                'error': {'message': 'Документ не найден'}
            }), 404
        
        doc = Document.from_row(row, table_name)
        
        # Проверка прав
        if not can_delete_document(current_user, doc):
            conn.close()
            return jsonify({
                'success': False,
                'error': {'message': 'Нет прав на удаление'}
            }), 403
        
        # Soft delete
        cursor.execute(f"UPDATE {table_name} SET status = 'deleted' WHERE id = ?", (doc_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Документ удален'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@documents_bp.route('/<int:doc_id>/download', methods=['GET'])
@login_required
def download_document(doc_id, current_user):
    """Скачивает файл документа"""
    try:
        category = request.args.get('category', 'internal')
        table_name = 'internal_documents' if category == 'internal' else 'external_documents'
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({
                'success': False,
                'error': {'message': 'Документ не найден'}
            }), 404
        
        doc = Document.from_row(row, table_name)
        
        # Проверка прав
        if not can_view_document(current_user, doc):
            return jsonify({
                'success': False,
                'error': {'message': 'Доступ запрещен'}
            }), 403
        
        # Полный путь к файлу
        file_path = BASE_DIR / doc.file_path
        
        if not file_path.exists():
            return jsonify({
                'success': False,
                'error': {'message': 'Файл не найден'}
            }), 404
        
        return send_file(
            str(file_path),
            as_attachment=True,
            download_name=doc.file_name
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500

