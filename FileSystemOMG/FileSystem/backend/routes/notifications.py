"""
Маршруты для работы с уведомлениями
"""
from flask import Blueprint, request, jsonify
from backend.models.notification import Notification
from backend.utils.middleware import login_required
from backend.utils.db import get_db_connection

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')


@notifications_bp.route('', methods=['GET'])
@login_required
def get_notifications(current_user):
    """Получает список уведомлений пользователя"""
    try:
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        
        notifications = Notification.get_user_notifications(
            current_user.id,
            unread_only=unread_only
        )
        
        return jsonify({
            'success': True,
            'notifications': [notif.to_dict() for notif in notifications]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@notifications_bp.route('/unread', methods=['GET'])
@login_required
def get_unread_notifications(current_user):
    """Получает непрочитанные уведомления"""
    try:
        notifications = Notification.get_user_notifications(
            current_user.id,
            unread_only=True
        )
        
        count = Notification.get_unread_count(current_user.id)
        
        return jsonify({
            'success': True,
            'count': count,
            'notifications': [notif.to_dict() for notif in notifications]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@notifications_bp.route('/<int:notif_id>/read', methods=['PUT'])
@login_required
def mark_as_read(notif_id, current_user):
    """Отмечает уведомление как прочитанное"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Проверяем, что уведомление принадлежит пользователю
        cursor.execute("""
            SELECT * FROM notifications 
            WHERE id = ? AND user_id = ?
        """, (notif_id, current_user.id))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({
                'success': False,
                'error': {'message': 'Уведомление не найдено'}
            }), 404
        
        notification = Notification.from_row(row)
        notification.mark_as_read()
        
        return jsonify({
            'success': True,
            'message': 'Уведомление отмечено как прочитанное'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500


@notifications_bp.route('/<int:notif_id>', methods=['DELETE'])
@login_required
def delete_notification(notif_id, current_user):
    """Удаляет уведомление"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Проверяем, что уведомление принадлежит пользователю
        cursor.execute("""
            SELECT * FROM notifications 
            WHERE id = ? AND user_id = ?
        """, (notif_id, current_user.id))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({
                'success': False,
                'error': {'message': 'Уведомление не найдено'}
            }), 404
        
        notification = Notification.from_row(row)
        notification.delete()
        
        return jsonify({
            'success': True,
            'message': 'Уведомление удалено'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500

