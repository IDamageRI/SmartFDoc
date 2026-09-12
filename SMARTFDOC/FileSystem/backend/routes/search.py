from flask import Blueprint, request, jsonify
from pathlib import Path
from backend.models.document import Document
from backend.utils.db import get_db_connection
from backend.utils.middleware import login_required
from backend.services.permissions import can_view_document
from backend.services.file_parser import extract_text_content
from backend.config import STORAGE_INTERNAL, STORAGE_EXTERNAL, BASE_DIR

search_bp = Blueprint('search', __name__, url_prefix='/api/search')


@search_bp.route('/catalog', methods=['GET'])
@login_required
def search_catalog(current_user):
    try:
        query = request.args.get('query', '').lower()
        category = request.args.get('category', 'internal')
        path = request.args.get('path', '')
        
        if category == 'internal':
            base_path = STORAGE_INTERNAL
        else:
            base_path = STORAGE_EXTERNAL
        
        if path:
            search_path = base_path / path
        else:
            search_path = base_path
        
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
        
        results = []
        
        def search_recursive(path_obj):
            try:
                for item in path_obj.iterdir():
                    if query in item.name.lower():
                        if item.is_file():
                            relative_path = str(item.relative_to(BASE_DIR))
                            
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            
                            if category == 'internal':
                                cursor.execute("""
                                    SELECT 'internal' as table_name, * FROM internal_documents 
                                    WHERE file_path LIKE ? AND status != 'deleted'
                                """, (f'%{relative_path}%',))
                            else:
                                cursor.execute("""
                                    SELECT 'external' as table_name, * FROM external_documents 
                                    WHERE file_path LIKE ? AND status != 'deleted'
                                """, (f'%{relative_path}%',))
                            
                            row = cursor.fetchone()
                            conn.close()
                            
                            if row:
                                doc = Document.from_row(row, row['table_name'])
                                if can_view_document(current_user, doc):
                                    results.append({
                                        'path': str(item.relative_to(base_path)),
                                        'name': item.name,
                                        'document': doc.to_dict()
                                    })
                        elif item.is_dir():
                            search_recursive(item)
            except PermissionError:
                pass
        
        search_recursive(search_path)
        
        return jsonify({
            'success': True,
            'items': results,
            'path': str(path) if path else ''
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@search_bp.route('/content', methods=['GET'])
@login_required
def search_content(current_user):
    try:
        query = request.args.get('query', '').strip().lower()
        category = request.args.get('category')
        department_id = request.args.get('department_id', type=int)
        type_id = request.args.get('type_id', type=int)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        tables = []
        if not category or category == '':
            tables.append('internal_documents')
            tables.append('external_documents')
        elif category == 'internal':
            tables.append('internal_documents')
        elif category == 'external':
            tables.append('external_documents')
        
        all_results = []
        
        for table_name in tables:
            print(f"Поиск в таблице: {table_name}, запрос: '{query}', категория: '{category}'")
            try:
                if table_name == 'external_documents':
                    sql = f"""
                        SELECT d.*, 
                               dt.name as document_type_name,
                               dept.name as department_name,
                               NULL as author_name
                        FROM {table_name} d
                        LEFT JOIN document_types dt ON d.document_type_id = dt.id
                        LEFT JOIN departments dept ON d.recipient_department_id = dept.id
                        WHERE d.status != 'deleted'
                    """
                else:
                    sql = f"""
                        SELECT d.*, 
                               dt.name as document_type_name,
                               dept.name as department_name,
                               u.full_name as author_name
                        FROM {table_name} d
                        LEFT JOIN document_types dt ON d.document_type_id = dt.id
                        LEFT JOIN departments dept ON d.department_id = dept.id OR d.recipient_department_id = dept.id
                        LEFT JOIN users u ON d.author_id = u.id
                        WHERE d.status != 'deleted'
                    """
                
                params = []
                
                if current_user.role == 'admin':
                    pass
                elif current_user.role == 'manager':
                    pass
                else:
                    if table_name == 'external_documents':
                        sql += " AND d.recipient_department_id = ?"
                        params.append(current_user.department_id)
                    else:
                        sql += " AND (d.department_id = ? OR d.recipient_department_id = ? OR d.author_id = ? OR d.recipient_user_id = ?)"
                        params.extend([
                            current_user.department_id,
                            current_user.department_id,
                            current_user.id,
                            current_user.id
                        ])
                
                if department_id:
                    if table_name == 'external_documents':
                        sql += " AND d.recipient_department_id = ?"
                        params.append(department_id)
                    else:
                        sql += " AND (d.department_id = ? OR d.recipient_department_id = ?)"
                        params.extend([department_id, department_id])
                
                if type_id:
                    sql += " AND d.document_type_id = ?"
                    params.append(type_id)
                
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                print(f"Найдено строк в {table_name}: {len(rows)}")
                
                for row in rows:
                    doc = Document.from_row(row, table_name)
                    
                    if not can_view_document(current_user, doc):
                        print(f"Документ {doc.id} из {table_name} не прошел проверку прав доступа")
                        continue
                    
                    doc_dict = doc.to_dict()
                    doc_dict['category'] = 'internal' if table_name == 'internal_documents' else 'external'
                    if not doc_dict.get('category'):
                        doc_dict['category'] = 'internal' if table_name == 'internal_documents' else 'external'
                    doc_dict['document_type_name'] = row['document_type_name'] if 'document_type_name' in row.keys() else None
                    doc_dict['department_name'] = row['department_name'] if 'department_name' in row.keys() else None
                    doc_dict['author_name'] = row['author_name'] if 'author_name' in row.keys() else None
                    
                    if table_name == 'external_documents':
                        if hasattr(doc, 'sender_name'):
                            doc_dict['sender_name'] = doc.sender_name
                        if hasattr(doc, 'sender_contact'):
                            doc_dict['sender_contact'] = doc.sender_contact
                        if hasattr(doc, 'sender_inn'):
                            doc_dict['sender_inn'] = doc.sender_inn
                        if hasattr(doc, 'sender_kpp'):
                            doc_dict['sender_kpp'] = doc.sender_kpp
                        if hasattr(doc, 'received_date'):
                            doc_dict['received_date'] = doc.received_date
                    
                    if query:
                        title_lower = (doc.title or '').lower().strip()
                        file_name_lower = (doc.file_name or '').lower().strip()
                        description_lower = (doc.description or '').lower().strip()
                        search_text = f"{title_lower} {description_lower} {file_name_lower}".strip()
                        if table_name == 'external_documents':
                            sender_name = (getattr(doc, 'sender_name', None) or '').lower().strip()
                            sender_inn = (getattr(doc, 'sender_inn', None) or '').lower().strip()
                            sender_kpp = (getattr(doc, 'sender_kpp', None) or '').lower().strip()
                            search_text += f" {sender_name} {sender_inn} {sender_kpp}".strip()
                        found_in_metadata = (query in search_text or 
                                           query in title_lower or 
                                           query in file_name_lower or
                                           (title_lower and title_lower.startswith(query)) or
                                           (file_name_lower and file_name_lower.startswith(query)))
                        
                        found_in_content = False
                        if doc.file_path:
                            try:
                                file_path_str = str(doc.file_path).replace('\\', '/')
                                if not file_path_str.startswith('storage/'):
                                    if table_name == 'internal_documents':
                                        file_path_str = f"storage/internal/{file_path_str}"
                                    else:
                                        file_path_str = f"storage/external/{file_path_str}"
                                
                                file_path = BASE_DIR / file_path_str
                                file_path = file_path.resolve()
                                
                                if file_path.exists() and file_path.is_file():
                                    file_content = extract_text_content(file_path)
                                    if file_content and query in file_content.lower():
                                        found_in_content = True
                            except Exception as e:
                                pass
                        
                        if not found_in_metadata and not found_in_content:
                            print(f"Документ {doc.id} из {table_name} не прошел проверку поиска (запрос: '{query}')")
                            continue
                    
                    print(f"Документ {doc.id} из {table_name} добавлен в результаты (категория: {doc_dict.get('category')})")
                    all_results.append(doc_dict)
            except Exception as e:
                import traceback
                print(f"Ошибка при поиске в таблице {table_name}: {e}")
                print(traceback.format_exc())
                continue
        
        conn.close()
        
        internal_count = len([r for r in all_results if r.get('category') != 'external'])
        external_count = len([r for r in all_results if r.get('category') == 'external'])
        print(f"Итого результатов: внутренние={internal_count}, внешние={external_count}, всего={len(all_results)}")
        
        return jsonify({
            'success': True,
            'documents': all_results
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500
