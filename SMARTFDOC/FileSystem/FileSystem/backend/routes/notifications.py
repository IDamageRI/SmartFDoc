from flask import Blueprint, request, jsonify
from backend.models.notification import Notification
from backend.utils.middleware import login_required
from backend.utils.db import get_db_connection

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')


@notifications_bp.route('', methods=['GET'])
@login_required
def get_notifications(current_user):
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
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM notifications 
            WHERE id = ? AND user_id = ?
        """, (notif_id, current_user.id))
        
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return jsonify({
                'success': False,
                'error': {'message': 'Уведомление не найдено'}
            }), 404
        
        cursor.execute("""
            UPDATE notifications 
            SET is_read = 1 
            WHERE id = ? AND user_id = ?
        """, (notif_id, current_user.id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500