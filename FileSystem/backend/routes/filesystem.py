from flask import Blueprint, request, jsonify
from pathlib import Path
from backend.config import STORAGE_INTERNAL, STORAGE_EXTERNAL, BASE_DIR
from backend.utils.middleware import login_required
from backend.services.permissions import can_view_document

filesystem_bp = Blueprint('filesystem', __name__, url_prefix='/api/filesystem')


def sanitize_name(name):
    if not name:
        return ""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    return name.strip()


def build_tree(path, base_path, current_user=None, documents_cache=None, allowed_departments=None):
    if not path.exists() or not path.is_dir():
        return None
    
    if path == base_path:
        tree_name = 'storage'
    else:
        tree_name = path.name
    
    relative_path = path.relative_to(base_path)
    path_parts = relative_path.parts if relative_path != Path('.') else []
    
    if len(path_parts) == 1 and current_user:
        if current_user.role == 'user':
            if allowed_departments is not None:
                dept_name_in_path = path_parts[0]
                if dept_name_in_path not in allowed_departments:
                    return None
    
    tree = {
        'name': tree_name,
        'path': str(path.relative_to(base_path)) if path != base_path else '',
        'type': 'directory',
        'children': []
    }
    
    try:
        items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
        
        for item in items:
            if item.is_dir():
                child_tree = build_tree(item, base_path, current_user, documents_cache, allowed_departments)
                if child_tree:
                    tree['children'].append(child_tree)
            else:
                file_info = {
                    'name': item.name,
                    'path': str(path.relative_to(base_path) / item.name) if path != base_path else item.name,
                    'type': 'file',
                    'size': item.stat().st_size
                }
                
                if documents_cache and current_user:
                    doc = documents_cache.get(str(item.relative_to(BASE_DIR)))
                    if doc:
                        if can_view_document(current_user, doc):
                            tree['children'].append(file_info)
                    else:
                        tree['children'].append(file_info)
                else:
                    tree['children'].append(file_info)
    
    except PermissionError:
        return None
    
    return tree


@filesystem_bp.route('/tree', methods=['GET'])
@login_required
def get_tree(current_user):
    try:
        category = request.args.get('category', 'internal')
        
        if category == 'internal':
            base_path = STORAGE_INTERNAL
        else:
            base_path = STORAGE_EXTERNAL
        
        allowed_departments = None
        if current_user.role == 'user':
            from backend.utils.db import get_db_connection
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if current_user.department_id:
                cursor.execute("SELECT name FROM departments WHERE id = ?", (current_user.department_id,))
                dept_row = cursor.fetchone()
                if dept_row:
                    dept_name = dept_row['name']
                    allowed_departments = [dept_name, sanitize_name(dept_name)]
            conn.close()
        
        tree = build_tree(base_path, base_path, current_user, None, allowed_departments)
        
        # Вместо корневого узла "storage" возвращаем сразу его дочерние узлы (отделы)
        if tree and tree.get('children'):
            # Возвращаем массив дочерних узлов вместо корневого узла
            return jsonify({
                'success': True,
                'tree': {
                    'name': 'root',
                    'path': '',
                    'type': 'directory',
                    'children': tree['children']
                },
                'category': category
            }), 200
        else:
            # Если нет дочерних узлов, возвращаем пустое дерево
            return jsonify({
                'success': True,
                'tree': {
                    'name': 'root',
                    'path': '',
                    'type': 'directory',
                    'children': []
                },
                'category': category
            }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@filesystem_bp.route('/path', methods=['GET'])
@login_required
def get_path_contents(current_user):
    try:
        category = request.args.get('category', 'internal')
        path_str = request.args.get('path', '')
        
        if category == 'internal':
            base_path = STORAGE_INTERNAL
        else:
            base_path = STORAGE_EXTERNAL
        
        full_path = base_path / path_str
        try:
            full_path = full_path.resolve()
            base_path_resolved = base_path.resolve()
            
            if not str(full_path).startswith(str(base_path_resolved)):
                return jsonify({
                    'success': False,
                    'error': {'message': 'Недопустимый путь'}
                }), 403
        except:
            return jsonify({
                'success': False,
                'error': {'message': 'Недопустимый путь'}
            }), 403
        
        if current_user.role == 'user':
            relative_path = full_path.relative_to(base_path)
            path_parts = relative_path.parts if relative_path != Path('.') else []
            
            if len(path_parts) > 0:
                dept_name_in_path = path_parts[0]
                from backend.utils.db import get_db_connection
                
                conn = get_db_connection()
                cursor = conn.cursor()
                
                if current_user.department_id:
                    cursor.execute("SELECT name FROM departments WHERE id = ?", (current_user.department_id,))
                    dept_row = cursor.fetchone()
                    if dept_row:
                        dept_name = dept_row['name']
                        if dept_name_in_path != dept_name and dept_name_in_path != sanitize_name(dept_name):
                            conn.close()
                            return jsonify({
                                'success': False,
                                'error': {'message': 'Доступ запрещен: вы можете просматривать только документы своего отдела'}
                            }), 403
                conn.close()
        
        if not full_path.exists():
            return jsonify({
                'success': False,
                'error': {'message': 'Путь не найден'}
            }), 404
        
        items = []
        
        if full_path.is_dir():
            try:
                for item in sorted(full_path.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
                    if current_user.role == 'user' and item.is_dir():
                        relative_item_path = item.relative_to(base_path)
                        item_parts = relative_item_path.parts if relative_item_path != Path('.') else []
                        
                        if len(item_parts) == 1:
                            dept_name_in_path = item_parts[0]
                            from backend.utils.db import get_db_connection
                            
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            
                            if current_user.department_id:
                                cursor.execute("SELECT name FROM departments WHERE id = ?", (current_user.department_id,))
                                dept_row = cursor.fetchone()
                                if dept_row:
                                    dept_name = dept_row['name']
                                    if dept_name_in_path != dept_name and dept_name_in_path != sanitize_name(dept_name):
                                        conn.close()
                                        continue  # Пропускаем этот отдел
                            conn.close()
                    
                    item_info = {
                        'name': item.name,
                        'path': str(item.relative_to(base_path)),
                        'type': 'file' if item.is_file() else 'directory',
                        'size': item.stat().st_size if item.is_file() else None
                    }
                    items.append(item_info)
            except PermissionError:
                return jsonify({
                    'success': False,
                    'error': {'message': 'Нет доступа к директории'}
                }), 403
        else:
            items.append({
                'name': full_path.name,
                'path': str(full_path.relative_to(base_path)),
                'type': 'file',
                'size': full_path.stat().st_size
            })
        
        return jsonify({
            'success': True,
            'path': path_str,
            'items': items,
            'category': category
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@filesystem_bp.route('/browse', methods=['GET'])
@login_required
def browse_filesystem(current_user):
    try:
        category = request.args.get('category', 'internal')
        path_str = request.args.get('path', '')
        
        if category == 'internal':
            base_path = STORAGE_INTERNAL
        else:
            base_path = STORAGE_EXTERNAL
        
        if not path_str:
            path = base_path
        else:
            path = base_path / path_str
            try:
                path = path.resolve()
                base_path_resolved = base_path.resolve()
                
                if not str(path).startswith(str(base_path_resolved)):
                    return jsonify({
                        'success': False,
                        'error': {'message': 'Недопустимый путь'}
                    }), 403
            except:
                return jsonify({
                    'success': False,
                    'error': {'message': 'Недопустимый путь'}
                }), 403
        
        if current_user.role == 'user':
            relative_path = path.relative_to(base_path)
            path_parts = relative_path.parts if relative_path != Path('.') else []
            
            if len(path_parts) > 0:
                dept_name_in_path = path_parts[0]
                from backend.utils.db import get_db_connection
                
                conn = get_db_connection()
                cursor = conn.cursor()
                
                if current_user.department_id:
                    cursor.execute("SELECT name FROM departments WHERE id = ?", (current_user.department_id,))
                    dept_row = cursor.fetchone()
                    if dept_row:
                        dept_name = dept_row['name']
                        if dept_name_in_path != dept_name and dept_name_in_path != sanitize_name(dept_name):
                            conn.close()
                            return jsonify({
                                'success': False,
                                'error': {'message': 'Доступ запрещен: вы можете просматривать только документы своего отдела'}
                            }), 403
                conn.close()
        
        if not path.exists():
            return jsonify({
                'success': False,
                'error': {'message': 'Путь не найден'}
            }), 404
        
        if not path.is_dir():
            return jsonify({
                'success': False,
                'error': {'message': 'Указанный путь не является директорией'}
            }), 400
        
        items = []
        try:
            for item in sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
                if current_user.role == 'user' and item.is_dir():
                    relative_item_path = item.relative_to(base_path)
                    item_parts = relative_item_path.parts if relative_item_path != Path('.') else []
                    
                    if len(item_parts) == 1:
                        dept_name_in_path = item_parts[0]
                        from backend.utils.db import get_db_connection
                        
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        
                        if current_user.department_id:
                            cursor.execute("SELECT name FROM departments WHERE id = ?", (current_user.department_id,))
                            dept_row = cursor.fetchone()
                            if dept_row:
                                dept_name = dept_row['name']
                                if dept_name_in_path != dept_name and dept_name_in_path != sanitize_name(dept_name):
                                    conn.close()
                                    continue  # Пропускаем этот отдел
                        conn.close()
                
                item_info = {
                    'name': item.name,
                    'path': str(item.relative_to(base_path)),
                    'type': 'file' if item.is_file() else 'directory',
                    'size': item.stat().st_size if item.is_file() else None
                }
                items.append(item_info)
        except PermissionError:
            return jsonify({
                'success': False,
                'error': {'message': 'Нет доступа к директории'}
            }), 403
        
        breadcrumbs = []
        current = path.relative_to(base_path)
        parts = current.parts if current != Path('.') else []
        
        breadcrumbs.append({
            'name': 'Корень',
            'path': ''
        })
        
        for i, part in enumerate(parts):
            breadcrumbs.append({
                'name': part,
                'path': str(Path(*parts[:i+1]))
            })
        
        return jsonify({
            'success': True,
            'path': path_str,
            'breadcrumbs': breadcrumbs,
            'items': items,
            'category': category
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500

