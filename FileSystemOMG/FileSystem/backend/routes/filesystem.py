"""
Маршруты для работы с файловой системой
"""
from flask import Blueprint, request, jsonify
from pathlib import Path
from backend.config import STORAGE_INTERNAL, STORAGE_EXTERNAL, BASE_DIR
from backend.utils.middleware import login_required
from backend.services.permissions import can_view_document

filesystem_bp = Blueprint('filesystem', __name__, url_prefix='/api/filesystem')


def build_tree(path, base_path, current_user=None, documents_cache=None):
    """
    Строит дерево файловой системы
    
    Args:
        path: Путь к директории
        base_path: Базовый путь (для относительных путей)
        current_user: Текущий пользователь (для фильтрации)
        documents_cache: Кэш документов для проверки прав
        
    Returns:
        dict: Структура дерева
    """
    if not path.exists() or not path.is_dir():
        return None
    
    # Для корневой директории используем специальное имя
    if path == base_path:
        tree_name = 'storage'
    else:
        tree_name = path.name
    
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
                child_tree = build_tree(item, base_path, current_user, documents_cache)
                if child_tree:
                    tree['children'].append(child_tree)
            else:
                # Это файл
                file_info = {
                    'name': item.name,
                    'path': str(path.relative_to(base_path) / item.name) if path != base_path else item.name,
                    'type': 'file',
                    'size': item.stat().st_size
                }
                
                # Если есть кэш документов, проверяем права доступа
                if documents_cache and current_user:
                    # Ищем документ по пути
                    doc = documents_cache.get(str(item.relative_to(BASE_DIR)))
                    if doc:
                        if can_view_document(current_user, doc):
                            tree['children'].append(file_info)
                    else:
                        # Если документ не найден в БД, все равно показываем
                        tree['children'].append(file_info)
                else:
                    tree['children'].append(file_info)
    
    except PermissionError:
        return None
    
    return tree


@filesystem_bp.route('/tree', methods=['GET'])
@login_required
def get_tree(current_user):
    """Получает древовидную структуру файловой системы"""
    try:
        category = request.args.get('category', 'internal')
        
        if category == 'internal':
            base_path = STORAGE_INTERNAL
        else:
            base_path = STORAGE_EXTERNAL
        
        # Строим дерево
        tree = build_tree(base_path, base_path, current_user)
        
        if not tree:
            # Если дерево пустое, возвращаем пустую структуру
            tree = {
                'name': 'storage',
                'path': '',
                'type': 'directory',
                'children': []
            }
        
        return jsonify({
            'success': True,
            'tree': tree,
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
    """Получает содержимое указанного пути"""
    try:
        category = request.args.get('category', 'internal')
        path_str = request.args.get('path', '')
        
        if category == 'internal':
            base_path = STORAGE_INTERNAL
        else:
            base_path = STORAGE_EXTERNAL
        
        # Безопасность: проверяем, что путь находится внутри base_path
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
        
        if not full_path.exists():
            return jsonify({
                'success': False,
                'error': {'message': 'Путь не найден'}
            }), 404
        
        items = []
        
        if full_path.is_dir():
            try:
                for item in sorted(full_path.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
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
            # Это файл
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
    """Просмотр файловой системы как файлового менеджера"""
    try:
        category = request.args.get('category', 'internal')
        path_str = request.args.get('path', '')
        
        if category == 'internal':
            base_path = STORAGE_INTERNAL
        else:
            base_path = STORAGE_EXTERNAL
        
        # Если путь не указан, возвращаем корень
        if not path_str:
            path = base_path
        else:
            path = base_path / path_str
            # Проверка безопасности
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
        
        # Получаем содержимое
        items = []
        try:
            for item in sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
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
        
        # Формируем breadcrumbs
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

