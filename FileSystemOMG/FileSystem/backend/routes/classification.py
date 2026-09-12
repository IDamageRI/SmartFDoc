"""
Маршруты для работы с правилами классификации
"""
from flask import Blueprint, request, jsonify
from backend.utils.middleware import login_required, admin_required
from backend.utils.db import get_db_connection

classification_bp = Blueprint('classification', __name__, url_prefix='/api/classification')


@classification_bp.route('/rules', methods=['GET'])
@admin_required
def get_rules(current_user):
    """Получает список правил классификации"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Проверяем существование таблицы
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='classification_rules'
        """)
        
        if not cursor.fetchone():
            # Таблица не существует, возвращаем пустой список
            return jsonify({
                'success': True,
                'rules': []
            }), 200
        
        cursor.execute("""
            SELECT id, name, condition_text, action_text, priority, is_active, created_at
            FROM classification_rules
            ORDER BY priority DESC, created_at DESC
        """)
        
        rules = []
        for row in cursor.fetchall():
            rules.append({
                'id': row['id'],
                'name': row['name'],
                'condition': row['condition_text'],
                'action': row['action_text'],
                'priority': row['priority'],
                'is_active': bool(row['is_active']),
                'created_at': row['created_at']
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'rules': rules
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@classification_bp.route('/rules', methods=['POST'])
@admin_required
def create_rule(current_user):
    """Создает новое правило классификации"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': {'message': 'Данные не предоставлены'}
            }), 400
        
        name = data.get('name')
        condition = data.get('condition')
        action = data.get('action')
        priority = data.get('priority', 'medium')
        
        if not name or not condition or not action:
            return jsonify({
                'success': False,
                'error': {'message': 'Название, условие и действие обязательны'}
            }), 400
        
        # Приоритет: high=3, medium=2, low=1
        priority_map = {'high': 3, 'medium': 2, 'low': 1}
        priority_value = priority_map.get(priority, 2)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Создаем таблицу если не существует
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS classification_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                condition_text TEXT NOT NULL,
                action_text TEXT NOT NULL,
                priority INTEGER DEFAULT 2,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            INSERT INTO classification_rules (name, condition_text, action_text, priority)
            VALUES (?, ?, ?, ?)
        """, (name, condition, action, priority_value))
        
        rule_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'rule_id': rule_id,
            'message': 'Правило успешно создано'
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@classification_bp.route('/rules/<int:rule_id>', methods=['PUT'])
@admin_required
def update_rule(rule_id, current_user):
    """Обновляет правило классификации"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': {'message': 'Данные не предоставлены'}
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if 'name' in data:
            updates.append('name = ?')
            params.append(data['name'])
        
        if 'condition' in data:
            updates.append('condition_text = ?')
            params.append(data['condition'])
        
        if 'action' in data:
            updates.append('action_text = ?')
            params.append(data['action'])
        
        if 'priority' in data:
            priority_map = {'high': 3, 'medium': 2, 'low': 1}
            priority_value = priority_map.get(data['priority'], 2)
            updates.append('priority = ?')
            params.append(priority_value)
        
        if 'is_active' in data:
            updates.append('is_active = ?')
            params.append(1 if data['is_active'] else 0)
        
        if not updates:
            return jsonify({
                'success': False,
                'error': {'message': 'Нет данных для обновления'}
            }), 400
        
        params.append(rule_id)
        
        cursor.execute(f"""
            UPDATE classification_rules 
            SET {', '.join(updates)}
            WHERE id = ?
        """, params)
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Правило обновлено'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@classification_bp.route('/rules/<int:rule_id>', methods=['DELETE'])
@admin_required
def delete_rule(rule_id, current_user):
    """Удаляет правило классификации"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM classification_rules WHERE id = ?", (rule_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Правило удалено'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500

