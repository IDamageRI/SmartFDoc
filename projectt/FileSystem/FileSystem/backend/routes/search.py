"""
Маршруты для поиска документов
"""
from flask import Blueprint, request, jsonify
from pathlib import Path
from backend.models.document import Document
from backend.utils.db import get_db_connection
from backend.utils.middleware import login_required
from backend.services.permissions import can_view_document
from backend.config import STORAGE_INTERNAL, STORAGE_EXTERNAL

search_bp = Blueprint('search', __name__, url_prefix='/api/search')


@search_bp.route('/catalog', methods=['GET'])
@login_required
def search_catalog(current_user):
    """Поиск по каталогам (файловой системе)"""
    try:
        query = request.args.get('query', '').lower()
        category = request.args.get('category', 'internal')
        path = request.args.get('path', '')
        
        if category == 'internal':
            base_path = STORAGE_INTERNAL
        else:
            base_path = STORAGE_EXTERNAL
        
        # Если указан путь, ищем в нем
        if path:
            search_path = base_path / path
        else:
            search_path = base_path
        
        # Проверка безопасности
        try:
            search_path = search_path.resolve()
            base_path_resolved = base_path.resolve()
            
            if not str(search_path).startswith(str(base_path_resolved)):
                return jsonify({
                    'success': False,
                    'error': {'message': 'Недопустимый путь'}
                }), 403
        except:
            return jsonify({
                'success': False,
                'error': {'message': 'Недопустимый путь'}
            }), 403
        
        if not search_path.exists():
            return jsonify({
                'success': False,
                'error': {'message': 'Путь не найден'}
            }), 404
        
        # Рекурсивный поиск
        results = []
        
        def search_recursive(path_obj):
            try:
                for item in path_obj.iterdir():
                    if query in item.name.lower():
                        # Проверяем, что это файл и есть в БД
                        if item.is_file():
                            # Ищем документ в БД по пути
                            relative_path = str(item.relative_to(Path(__file__).parent.parent.parent))
                            
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            
                            # Ищем в обеих таблицах
                            cursor.execute("""
                                SELECT 'internal' as table_name, * FROM internal_documents 
                                WHERE file_path LIKE ?
                                UNION ALL
                                SELECT 'external' as table_name, * FROM external_documents 
                                WHERE file_path LIKE ?
                            """, (f'%{item.name}%', f'%{item.name}%'))
                            
                            row = cursor.fetchone()
                            conn.close()
                            
                            if row:
                                doc = Document.from_row(row, row['table_name'])
                                if can_view_document(current_user, doc):
                                    results.append({
                                        'name': item.name,
                                        'path': str(item.relative_to(base_path)),
                                        'type': 'file',
                                        'size': item.stat().st_size,
                                        'document_id': doc.id,
                                        'category': row['table_name']
                                    })
                    
                    if item.is_dir():
                        search_recursive(item)
            except PermissionError:
                pass
        
        if search_path.is_dir():
            search_recursive(search_path)
        elif query in search_path.name.lower():
            results.append({
                'name': search_path.name,
                'path': str(search_path.relative_to(base_path)),
                'type': 'file',
                'size': search_path.stat().st_size
            })
        
        return jsonify({
            'success': True,
            'query': query,
            'results': results,
            'count': len(results)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@search_bp.route('/content', methods=['GET'])
@login_required
def search_content(current_user):
    """Поиск по содержимому документов (метаданным)"""
    try:
        query = request.args.get('query', '').strip().lower()
        category = request.args.get('category')
        department_id = request.args.get('department_id', type=int)
        type_id = request.args.get('type_id', type=int)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Определяем таблицы для поиска
        tables = []
        if not category or category == 'internal':
            tables.append('internal_documents')
        if not category or category == 'external':
            tables.append('external_documents')
        
        all_results = []
        
        for table_name in tables:
            # Базовый запрос
            if query:
                # Если есть запрос - ищем по содержимому
                sql = f"""
                    SELECT d.*, 
                           dt.name as document_type_name,
                           dept.name as department_name,
                           u.full_name as author_name
                    FROM {table_name} d
                    LEFT JOIN document_types dt ON d.document_type_id = dt.id
                    LEFT JOIN departments dept ON d.department_id = dept.id OR d.recipient_department_id = dept.id
                    LEFT JOIN users u ON d.author_id = u.id
                    WHERE d.status = 'active'
                    AND (
                        LOWER(d.title) LIKE ? OR
                        LOWER(d.description) LIKE ? OR
                        LOWER(d.file_name) LIKE ?
                    )
                """
                params = [f'%{query}%', f'%{query}%', f'%{query}%']
            else:
                # Если запроса нет - показываем все документы
                sql = f"""
                    SELECT d.*, 
                           dt.name as document_type_name,
                           dept.name as department_name,
                           u.full_name as author_name
                    FROM {table_name} d
                    LEFT JOIN document_types dt ON d.document_type_id = dt.id
                    LEFT JOIN departments dept ON d.department_id = dept.id OR d.recipient_department_id = dept.id
                    LEFT JOIN users u ON d.author_id = u.id
                    WHERE d.status = 'active'
                """
                params = []
            
            # Фильтры по правам доступа
            # Внешние документы доступны всем
            if table_name == 'external_documents':
                # Внешние документы доступны всем пользователям
                pass
            elif current_user.role == 'admin':
                # Администратор видит все
                pass
            elif current_user.role == 'manager':
                # Руководитель видит документы своего отдела
                sql += " AND (d.department_id = ? OR d.recipient_department_id = ?)"
                params.extend([current_user.department_id, current_user.department_id])
            else:
                # Обычный сотрудник видит документы отдела + личные
                sql += " AND (d.department_id = ? OR d.recipient_department_id = ? OR d.author_id = ? OR d.recipient_user_id = ?)"
                params.extend([
                    current_user.department_id,
                    current_user.department_id,
                    current_user.id,
                    current_user.id
                ])
            
            # Дополнительные фильтры
            if department_id:
                sql += " AND (d.department_id = ? OR d.recipient_department_id = ?)"
                params.extend([department_id, department_id])
            
            if type_id:
                sql += " AND d.document_type_id = ?"
                params.append(type_id)
            
            sql += " ORDER BY d.created_at DESC"
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            for row in rows:
                doc = Document.from_row(row, table_name)
                if can_view_document(current_user, doc):
                    doc_dict = doc.to_dict()
                    doc_dict['category'] = 'internal' if table_name == 'internal_documents' else 'external'
                    doc_dict['document_type_name'] = row['document_type_name'] if 'document_type_name' in row.keys() else None
                    doc_dict['department_name'] = row['department_name'] if 'department_name' in row.keys() else None
                    doc_dict['author_name'] = row['author_name'] if 'author_name' in row.keys() else None
                    all_results.append(doc_dict)
        
        conn.close()
        
        # Ранжируем результаты по релевантности
        from backend.services.search_engine import rank_search_results
        if query:
            all_results = rank_search_results(query, all_results)
        
        return jsonify({
            'success': True,
            'query': query,
            'results': all_results,
            'count': len(all_results)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500

