"""
Маршруты статистики (только для администратора)
"""
from flask import Blueprint, request, jsonify
from backend.utils.db import get_db_connection
from backend.utils.middleware import login_required, admin_required

stats_bp = Blueprint('stats', __name__, url_prefix='/api/stats')


@stats_bp.route('/overview', methods=['GET'])
@admin_required
def get_overview(current_user):
    """Получает общую статистику"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Всего документов
        cursor.execute("SELECT COUNT(*) as count FROM internal_documents WHERE status = 'active'")
        internal_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM external_documents WHERE status = 'active'")
        external_count = cursor.fetchone()['count']
        
        total_documents = internal_count + external_count
        
        # Документы по статусам
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM (
                SELECT status FROM internal_documents
                UNION ALL
                SELECT status FROM external_documents
            )
            GROUP BY status
        """)
        status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
        
        # Документы с истекающими сроками
        from datetime import datetime, timedelta
        today = datetime.now().date()
        in_3_days = today + timedelta(days=3)
        in_1_day = today + timedelta(days=1)
        
        cursor.execute("""
            SELECT COUNT(*) as count FROM internal_documents 
            WHERE expiry_date IS NOT NULL 
            AND expiry_date <= ? AND expiry_date >= ?
            AND status = 'active'
        """, (in_3_days, today))
        expiring_soon = cursor.fetchone()['count']
        
        cursor.execute("""
            SELECT COUNT(*) as count FROM external_documents 
            WHERE expiry_date IS NOT NULL 
            AND expiry_date <= ? AND expiry_date >= ?
            AND status = 'active'
        """, (in_3_days, today))
        expiring_soon += cursor.fetchone()['count']
        
        # Документы по типам
        cursor.execute("""
            SELECT dt.name, COUNT(*) as count
            FROM internal_documents d
            LEFT JOIN document_types dt ON d.document_type_id = dt.id
            WHERE d.status = 'active'
            GROUP BY dt.name
            ORDER BY count DESC
            LIMIT 10
        """)
        types_internal = cursor.fetchall()
        
        cursor.execute("""
            SELECT dt.name, COUNT(*) as count
            FROM external_documents d
            LEFT JOIN document_types dt ON d.document_type_id = dt.id
            WHERE d.status = 'active'
            GROUP BY dt.name
            ORDER BY count DESC
            LIMIT 10
        """)
        types_external = cursor.fetchall()
        
        # Объединяем типы
        type_counts = {}
        for row in types_internal:
            name = row['name'] or 'Без типа'
            type_counts[name] = type_counts.get(name, 0) + row['count']
        for row in types_external:
            name = row['name'] or 'Без типа'
            type_counts[name] = type_counts.get(name, 0) + row['count']
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_documents': total_documents,
                'internal_documents': internal_count,
                'external_documents': external_count,
                'status_counts': status_counts,
                'expiring_soon': expiring_soon,
                'document_types': type_counts
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@stats_bp.route('/departments', methods=['GET'])
@admin_required
def get_department_stats(current_user):
    """Получает статистику по отделам"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Документы по отделам (внутренние)
        cursor.execute("""
            SELECT d.name, COUNT(doc.id) as count
            FROM departments d
            LEFT JOIN internal_documents doc ON doc.department_id = d.id AND doc.status = 'active'
            GROUP BY d.id, d.name
            ORDER BY count DESC
        """)
        dept_internal = {row['name']: row['count'] for row in cursor.fetchall()}
        
        # Документы по отделам (внешние - получатели)
        cursor.execute("""
            SELECT d.name, COUNT(doc.id) as count
            FROM departments d
            LEFT JOIN external_documents doc ON doc.recipient_department_id = d.id AND doc.status = 'active'
            GROUP BY d.id, d.name
            ORDER BY count DESC
        """)
        dept_external = {row['name']: row['count'] for row in cursor.fetchall()}
        
        # Объединяем
        all_depts = set(dept_internal.keys()) | set(dept_external.keys())
        department_stats = []
        total = 0
        
        for dept_name in all_depts:
            count = dept_internal.get(dept_name, 0) + dept_external.get(dept_name, 0)
            total += count
            department_stats.append({
                'name': dept_name,
                'count': count
            })
        
        # Добавляем проценты
        for stat in department_stats:
            stat['percentage'] = round((stat['count'] / total * 100) if total > 0 else 0, 1)
        
        department_stats.sort(key=lambda x: x['count'], reverse=True)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'departments': department_stats,
            'total': total
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@stats_bp.route('/sources', methods=['GET'])
@admin_required
def get_sources_stats(current_user):
    """Получает статистику по источникам документов"""
    try:
        # В текущей версии источники не хранятся отдельно
        # Можно добавить поле source в таблицы документов в будущем
        # Пока возвращаем базовую информацию
        
        return jsonify({
            'success': True,
            'sources': [
                {
                    'name': 'Внутренние документы',
                    'count': 'internal',
                    'description': 'Документы, созданные внутри компании'
                },
                {
                    'name': 'Внешние документы',
                    'count': 'external',
                    'description': 'Документы, полученные извне'
                }
            ]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500

