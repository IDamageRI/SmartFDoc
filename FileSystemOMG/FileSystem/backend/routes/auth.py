"""
Маршруты авторизации
"""
import traceback
from flask import Blueprint, request, jsonify, session
from backend.models.user import User

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/login', methods=['POST', 'OPTIONS'])
def login():
    """Авторизация пользователя"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        data = request.get_json()
    except Exception as e:
        return jsonify({'success': False, 'error': {'message': f'Ошибка парсинга данных: {str(e)}'}}), 400
    
    if not data:
        return jsonify({'success': False, 'error': {'message': 'Данные не предоставлены'}}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({
            'success': False,
            'error': {'message': 'Логин и пароль обязательны'}
        }), 400
    
    try:
        # Находим пользователя
        user = User.find_by_username(username)
        
        if not user:
            return jsonify({
                'success': False,
                'error': {'message': 'Неверный логин или пароль'}
            }), 401
        
        # Проверяем пароль
        if not user.verify_password(password):
            return jsonify({
                'success': False,
                'error': {'message': 'Неверный логин или пароль'}
            }), 401
        
        # Сохраняем в сессию
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        
        return jsonify({
            'success': True,
            'user': user.to_dict(),
            'session_id': session.get('user_id')
        }), 200
    except Exception as e:
        print(f"Ошибка при авторизации: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': {'message': f'Внутренняя ошибка сервера: {str(e)}'}
        }), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Выход из системы"""
    session.clear()
    return jsonify({'success': True}), 200


@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Получает информацию о текущем пользователе"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({
            'success': False,
            'error': {'message': 'Не авторизован'}
        }), 401
    
    user = User.find_by_id(user_id)
    
    if not user:
        session.clear()
        return jsonify({
            'success': False,
            'error': {'message': 'Пользователь не найден'}
        }), 404
    
    return jsonify({
        'success': True,
        'user': user.to_dict()
    }), 200

