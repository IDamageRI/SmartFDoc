from flask import Blueprint, request, jsonify
from pathlib import Path
from urllib.parse import unquote
from backend.config import STORAGE_INTERNAL, STORAGE_EXTERNAL, BASE_DIR
from backend.utils.middleware import login_required
from backend.services.file_parser import parse_file

file_parser_bp = Blueprint('file_parser', __name__, url_prefix='/api/file-parser')


@file_parser_bp.route('/parse', methods=['GET'])
@login_required
def parse_file_content(current_user):
    try:
        category = request.args.get('category', 'internal')
        file_path = request.args.get('path', '')
        
        if not file_path:
            return jsonify({
                'success': False,
                'error': 'Не указан путь к файлу'
            }), 400
        
        if category == 'internal':
            base_path = STORAGE_INTERNAL
        else:
            base_path = STORAGE_EXTERNAL
        
        decoded_path = file_path
        if decoded_path.startswith('internal/'):
            decoded_path = decoded_path[9:]  # Убираем 'internal/'
        elif decoded_path.startswith('external/'):
            decoded_path = decoded_path[9:]  # Убираем 'external/'
        
        try:
            path_parts = decoded_path.split('/')
            decoded_parts = [unquote(part) for part in path_parts]
            decoded_path = '/'.join(decoded_parts)
        except:
            pass  # Используем как есть
        
        if decoded_path:
            full_path = base_path / decoded_path
        else:
            full_path = base_path
        
        try:
            full_path = full_path.resolve()
            base_path_resolved = base_path.resolve()
            
            if not str(full_path).startswith(str(base_path_resolved)):
                return jsonify({
                    'success': False,
                    'error': 'Недопустимый путь'
                }), 403
        except:
            return jsonify({
                'success': False,
                'error': 'Недопустимый путь'
            }), 403
        
        result = parse_file(full_path)
        
        if result['success']:
            return jsonify({
                'success': True,
                'html': result['html'],
                'error': None
            }), 200
        else:
            return jsonify({
                'success': False,
                'html': '',
                'error': result['error']
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'html': '',
            'error': f'Ошибка сервера: {str(e)}'
        }), 500

