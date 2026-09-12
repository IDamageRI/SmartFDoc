"""
Middleware для проверки авторизации
"""
from functools import wraps
from flask import session, jsonify
from backend.models.user import User


def login_required(f):
    """Декоратор для проверки авторизации"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': {'message': 'Требуется авторизация'}
            }), 401
        
        # Проверяем, что пользователь существует
        user = User.find_by_id(user_id)
        if not user:
            session.clear()
            return jsonify({
                'success': False,
                'error': {'message': 'Пользователь не найден'}
            }), 401
        
        # Добавляем пользователя в kwargs
        kwargs['current_user'] = user
        return f(*args, **kwargs)
    
    return decorated_function


def admin_required(f):
    """Декоратор для проверки прав администратора"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        user = kwargs.get('current_user')
        if user.role != 'admin':
            return jsonify({
                'success': False,
                'error': {'message': 'Требуются права администратора'}
            }), 403
        return f(*args, **kwargs)
    
    return decorated_function

