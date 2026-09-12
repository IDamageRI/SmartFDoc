"""
Главный файл Flask приложения
"""
from flask import Flask, send_from_directory, request, send_file, jsonify
from pathlib import Path
from backend.config import BASE_DIR, SECRET_KEY
from backend.utils.db import init_db
from backend.routes.auth import auth_bp
from backend.routes.references import references_bp
from backend.routes.documents import documents_bp
from backend.routes.notifications import notifications_bp
from backend.routes.filesystem import filesystem_bp
from backend.routes.search import search_bp
from backend.routes.stats import stats_bp
from backend.routes.classification import classification_bp
from backend.routes.admin import admin_bp

# Создаем приложение
app = Flask(__name__, static_folder=None)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Для работы с localhost
app.config['SESSION_COOKIE_SECURE'] = False  # True для HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True

# CORS для работы с фронтендом
@app.after_request
def after_request(response):
    """Добавляет CORS заголовки"""
    origin = request.headers.get('Origin')
    if origin:
        response.headers.add('Access-Control-Allow-Origin', origin)
    else:
        response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# Обработка OPTIONS запросов для CORS
@app.before_request
def handle_preflight():
    """Обрабатывает preflight запросы"""
    if request.method == "OPTIONS":
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin')
        if origin:
            response.headers.add('Access-Control-Allow-Origin', origin)
        else:
            response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

# Регистрируем blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(references_bp)
app.register_blueprint(documents_bp)
app.register_blueprint(notifications_bp)
app.register_blueprint(filesystem_bp)
app.register_blueprint(search_bp)
app.register_blueprint(stats_bp)
app.register_blueprint(classification_bp)
app.register_blueprint(admin_bp)

# Инициализация БД (выполняется при импорте модуля)
try:
    init_db()
except Exception as e:
    print(f"Ошибка инициализации БД: {e}")


# Эндпоинт для проверки доступности сервера
@app.route('/api/health', methods=['GET'])
def health_check():
    """Проверка доступности сервера"""
    return jsonify({
        'status': 'ok',
        'message': 'Сервер работает'
    }), 200

# Раздача статических файлов (фронтенд)
@app.route('/')
def index():
    """Главная страница"""
    return send_from_directory(str(BASE_DIR / 'frontend'), 'index.html')


@app.route('/storage/<path:file_path>')
def serve_storage_file(file_path):
    """Раздача файлов из storage с правильной обработкой кириллицы"""
    from urllib.parse import unquote
    
    # Декодируем URL-encoded путь
    try:
        decoded_path = unquote(file_path)
        # Заменяем обратные слеши на прямые для Windows
        decoded_path = decoded_path.replace('\\', '/')
    except Exception:
        decoded_path = file_path
    
    storage_path = BASE_DIR / 'storage' / decoded_path
    
    if storage_path.exists() and storage_path.is_file():
        try:
            # Проверяем, что файл действительно в storage
            storage_dir = BASE_DIR / 'storage'
            storage_path.resolve().relative_to(storage_dir.resolve())
            
            # Устанавливаем правильные заголовки для кириллицы
            response = send_file(
                str(storage_path),
                as_attachment=False,
                download_name=storage_path.name
            )
            # Добавляем заголовки для правильной кодировки
            response.headers['Content-Disposition'] = f'inline; filename="{storage_path.name}"'
            return response
        except (ValueError, OSError) as e:
            return jsonify({'error': 'Invalid path', 'details': str(e)}), 403
    
    return jsonify({'error': 'File not found'}), 404


@app.route('/<path:path>')
def serve_static(path):
    """Раздача статических файлов из frontend"""
    # Проверяем файлы из frontend
    frontend_path = BASE_DIR / 'frontend' / path
    if frontend_path.exists() and frontend_path.is_file():
        return send_from_directory(str(BASE_DIR / 'frontend'), path)
    
    return {'error': 'Not found'}, 404


# Обработка ошибок
@app.errorhandler(404)
def not_found(error):
    return {'error': 'Not found'}, 404


@app.errorhandler(500)
def internal_error(error):
    return {'error': 'Internal server error'}, 500


if __name__ == '__main__':
    # Инициализируем БД
    try:
        init_db()
    except Exception as e:
        print(f"Ошибка инициализации БД: {e}")
    
    # Запускаем сервер
    app.run(debug=True, host='0.0.0.0', port=5000)

