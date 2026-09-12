from flask import Blueprint, request, jsonify
from backend.services.duplicate_detector import duplicate_detector
from backend.utils.middleware import login_required
from backend.utils.db import get_db_connection

duplicates_bp = Blueprint('duplicates', __name__, url_prefix='/api/duplicates')


@duplicates_bp.route('', methods=['GET'])
@login_required
def get_duplicates(current_user):
    try:
        method = request.args.get('method', 'hash')  # hash, filename, metadata
        category = request.args.get('category')  # internal, external, None=all
        department_id = request.args.get('department_id', type=int)
        
        if current_user.role not in ['admin', 'manager']:
            return jsonify({
                'success': False,
                'error': {'message': 'Недостаточно прав для просмотра дубликатов'}
            }), 403
        
        duplicates = duplicate_detector.find_duplicates(
            method=method,
            category=category,
            department_id=department_id
        )
        
        report = duplicate_detector.get_duplicates_report(duplicates)
        
        return jsonify({
            'success': True,
            'report': report
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': f'Ошибка при поиске дубликатов: {str(e)}'}
        }), 500


@duplicates_bp.route('/resolve', methods=['POST'])
@login_required
def resolve_duplicates(current_user):
    try:
        data = request.json
        group_id = data.get('group_id')
        keep_document_id = data.get('keep_document_id')
        delete_document_ids = data.get('delete_document_ids', [])
        
        if current_user.role != 'admin':
            return jsonify({
                'success': False,
                'error': {'message': 'Недостаточно прав для удаления документов'}
            }), 403
        
        if not keep_document_id or not delete_document_ids:
            return jsonify({
                'success': False,
                'error': {'message': 'Не указаны документы для сохранения/удаления'}
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        deleted_count = 0
        errors = []
        
        for doc_id in delete_document_ids:
            try:
                cursor.execute("SELECT id FROM internal_documents WHERE id = ? AND status = 'active'", (doc_id,))
                if cursor.fetchone():
                    cursor.execute("UPDATE internal_documents SET status = 'deleted' WHERE id = ?", (doc_id,))
                    deleted_count += 1
                    continue
                
                cursor.execute("SELECT id FROM external_documents WHERE id = ? AND status = 'active'", (doc_id,))
                if cursor.fetchone():
                    cursor.execute("UPDATE external_documents SET status = 'deleted' WHERE id = ?", (doc_id,))
                    deleted_count += 1
                    continue
                
                errors.append(f"Документ {doc_id} не найден")
                
            except Exception as e:
                errors.append(f"Ошибка удаления документа {doc_id}: {str(e)}")
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Удалено {deleted_count} дубликатов',
            'deleted_count': deleted_count,
            'errors': errors if errors else None
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': f'Ошибка при разрешении дубликатов: {str(e)}'}
        }), 500


@duplicates_bp.route('/stats', methods=['GET'])
@login_required
def get_duplicates_stats(current_user):
    try:
        if current_user.role not in ['admin', 'manager']:
            return jsonify({
                'success': False,
                'error': {'message': 'Недостаточно прав для просмотра статистики'}
            }), 403
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT file_name) as unique_names,
                   COUNT(*) - COUNT(DISTINCT file_name) as name_duplicates
            FROM internal_documents 
            WHERE status = 'active'
        """)
        internal_stats = cursor.fetchone()
        
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT file_name) as unique_names,
                   COUNT(*) - COUNT(DISTINCT file_name) as name_duplicates
            FROM external_documents 
            WHERE status = 'active'
        """)
        external_stats = cursor.fetchone()
        
        total_documents = (internal_stats['total'] or 0) + (external_stats['total'] or 0)
        unique_names = (internal_stats['unique_names'] or 0) + (external_stats['unique_names'] or 0)
        name_duplicates = (internal_stats['name_duplicates'] or 0) + (external_stats['name_duplicates'] or 0)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_documents': total_documents,
                'unique_names': unique_names,
                'name_duplicates': name_duplicates
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500