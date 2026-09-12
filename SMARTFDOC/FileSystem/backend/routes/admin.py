"""
Маршруты админ-панели
"""
from flask import Blueprint, jsonify, request
from backend.utils.middleware import admin_required
from backend.utils.db import get_db_connection
from backend.config import DATABASE_PATH, BASE_DIR
from pathlib import Path
import shutil
import zipfile
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users(current_user):
    """Получает список всех пользователей"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.id, u.username, u.full_name as name, u.email, u.role, 
                   u.department_id, u.created_at,
                   d.name as department_name
            FROM users u
            LEFT JOIN departments d ON u.department_id = d.id
            ORDER BY u.id
        """)
        
        rows = cursor.fetchall()
        users = []
        for row in rows:
            users.append({
                'id': row['id'],
                'username': row['username'],
                'name': row['name'],
                'email': row['email'],
                'role': row['role'],
                'department_id': row['department_id'],
                'department_name': row['department_name'],
                'created_at': row['created_at']
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'users': users
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@admin_bp.route('/users', methods=['POST'])
@admin_required
def create_user(current_user):
    """Создает нового пользователя"""
    try:
        data = request.get_json()
        
        username = data.get('username', '').strip() if data.get('username') else ''
        full_name = data.get('full_name', '').strip() if data.get('full_name') else ''
        email = data.get('email', '').strip() if data.get('email') else None
        department_id = data.get('department_id')
        if department_id is not None and department_id != '':
            try:
                department_id = int(department_id)
            except (ValueError, TypeError):
                department_id = None
        else:
            department_id = None
        role = data.get('role', 'user')
        password = data.get('password', '123')  # По умолчанию пароль 123
        
        if not username or not full_name:
            return jsonify({
                'success': False,
                'message': 'Логин и имя обязательны'
            }), 400
        
        if role not in ['admin', 'manager', 'user']:
            return jsonify({
                'success': False,
                'message': 'Недопустимая роль'
            }), 400
        
        from backend.utils.validators import hash_password
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Включаем поддержку внешних ключей
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Проверяем, не существует ли пользователь
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Пользователь с таким логином уже существует'
            }), 400
        
        # Проверяем отдел, если указан
        if department_id:
            cursor.execute("SELECT id FROM departments WHERE id = ?", (department_id,))
            if not cursor.fetchone():
                conn.close()
                return jsonify({
                    'success': False,
                    'message': 'Отдел не найден'
                }), 400
        
        password_hash = hash_password(password)
        
        try:
            cursor.execute("""
                INSERT INTO users (username, full_name, email, department_id, role, password_hash)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (username, full_name, email, department_id, role, password_hash))
            
            user_id = cursor.lastrowid
            conn.commit()
        except Exception as e:
            conn.rollback()
            conn.close()
            return jsonify({
                'success': False,
                'message': f'Ошибка создания пользователя: {str(e)}'
            }), 500
        
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Пользователь создан',
            'user_id': user_id
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id, current_user):
    """Обновляет пользователя"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'Данные не предоставлены'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Включаем поддержку внешних ключей
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Проверяем существование пользователя
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Пользователь не найден'
            }), 404
        
        updates = []
        params = []
        
        if 'full_name' in data and data['full_name']:
            updates.append('full_name = ?')
            params.append(data['full_name'].strip())
        
        if 'email' in data:
            # Позволяем установить email в NULL
            updates.append('email = ?')
            params.append(data['email'].strip() if data['email'] else None)
        
        if 'department_id' in data:
            # Позволяем установить department_id в NULL
            dept_id = data['department_id']
            if dept_id is not None and dept_id != '':
                try:
                    dept_id = int(dept_id)
                    # Проверяем существование отдела
                    cursor.execute("SELECT id FROM departments WHERE id = ?", (dept_id,))
                    if not cursor.fetchone():
                        conn.close()
                        return jsonify({
                            'success': False,
                            'message': 'Отдел не найден'
                        }), 400
                except (ValueError, TypeError):
                    dept_id = None
            else:
                dept_id = None
            updates.append('department_id = ?')
            params.append(dept_id)
        
        if 'role' in data:
            if data['role'] not in ['admin', 'manager', 'user']:
                conn.close()
                return jsonify({
                    'success': False,
                    'message': 'Недопустимая роль'
                }), 400
            updates.append('role = ?')
            params.append(data['role'])
        
        if 'password' in data and data['password']:
            from backend.utils.validators import hash_password
            updates.append('password_hash = ?')
            params.append(hash_password(data['password']))
        
        if not updates:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Нет данных для обновления'
            }), 400
        
        updates.append('updated_at = CURRENT_TIMESTAMP')
        params.append(user_id)
        
        cursor.execute(f"""
            UPDATE users 
            SET {', '.join(updates)}
            WHERE id = ?
        """, params)
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Пользователь обновлен'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id, current_user):
    """Удаляет пользователя"""
    try:
        # Нельзя удалить самого себя
        if user_id == current_user.id:
            return jsonify({
                'success': False,
                'message': 'Нельзя удалить самого себя'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Отключаем проверку внешних ключей, чтобы можно было удалить пользователя
        # при сохранении метаданных (author_id и recipient_user_id остаются в документах)
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # Проверяем существование пользователя
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Пользователь не найден'
            }), 404
        
        # Метаданные документов сохраняются (author_id и recipient_user_id остаются без изменений)
        # Удаляем только уведомления пользователя
        cursor.execute("DELETE FROM notifications WHERE user_id = ?", (user_id,))
        
        # Удаляем пользователя (метаданные в документах сохраняются)
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Пользователь удален'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@admin_bp.route('/departments', methods=['GET'])
@admin_required
def get_departments(current_user):
    """Получает список всех отделов"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM departments ORDER BY id")
        rows = cursor.fetchall()
        
        departments = []
        for row in rows:
            departments.append({
                'id': row['id'],
                'name': row['name'],
                'description': row['description'],
                'created_at': row['created_at']
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'departments': departments
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@admin_bp.route('/departments', methods=['POST'])
@admin_required
def create_department(current_user):
    """Создает новый отдел"""
    try:
        data = request.get_json()
        
        name = data.get('name', '').strip()
        description = data.get('description', '').strip() if data.get('description') else None
        
        if not name:
            return jsonify({
                'success': False,
                'message': 'Название отдела обязательно'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Проверяем, не существует ли отдел
        cursor.execute("SELECT id FROM departments WHERE name = ?", (name,))
        if cursor.fetchone():
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Отдел с таким названием уже существует'
            }), 400
        
        cursor.execute("""
            INSERT INTO departments (name, description)
            VALUES (?, ?)
        """, (name, description))
        
        dept_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Отдел создан',
            'department_id': dept_id
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@admin_bp.route('/departments/<int:dept_id>', methods=['PUT'])
@admin_required
def update_department(dept_id, current_user):
    """Обновляет отдел"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'Данные не предоставлены'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Проверяем существование отдела
        cursor.execute("SELECT id FROM departments WHERE id = ?", (dept_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Отдел не найден'
            }), 404
        
        updates = []
        params = []
        
        if 'name' in data and data['name']:
            # Проверяем уникальность названия
            cursor.execute("SELECT id FROM departments WHERE name = ? AND id != ?", (data['name'], dept_id))
            if cursor.fetchone():
                conn.close()
                return jsonify({
                    'success': False,
                    'message': 'Отдел с таким названием уже существует'
                }), 400
            updates.append('name = ?')
            params.append(data['name'].strip())
        
        if 'description' in data:
            updates.append('description = ?')
            params.append(data['description'].strip() if data['description'] else None)
        
        if not updates:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Нет данных для обновления'
            }), 400
        
        params.append(dept_id)
        
        cursor.execute(f"""
            UPDATE departments 
            SET {', '.join(updates)}
            WHERE id = ?
        """, params)
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Отдел обновлен'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@admin_bp.route('/departments/<int:dept_id>', methods=['DELETE'])
@admin_required
def delete_department(dept_id, current_user):
    """Удаляет отдел вместе со всеми его директориями, файлами и метаданными"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Включаем поддержку внешних ключей
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Получаем название отдела для поиска директорий
        cursor.execute("SELECT name FROM departments WHERE id = ?", (dept_id,))
        dept_row = cursor.fetchone()
        if not dept_row:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Отдел не найден'
            }), 404
        
        dept_name = dept_row['name']
        
        # Находим все документы отдела (внутренние и внешние)
        cursor.execute("""
            SELECT id, file_path, 'internal' as category 
            FROM internal_documents 
            WHERE department_id = ? OR recipient_department_id = ?
        """, (dept_id, dept_id))
        internal_docs = cursor.fetchall()
        
        cursor.execute("""
            SELECT id, file_path, 'external' as category 
            FROM external_documents 
            WHERE recipient_department_id = ?
        """, (dept_id,))
        external_docs = cursor.fetchall()
        
        all_docs = list(internal_docs) + list(external_docs)
        
        # Удаляем физические файлы
        deleted_files = 0
        for doc in all_docs:
            try:
                file_path = BASE_DIR / 'storage' / doc['file_path']
                if file_path.exists() and file_path.is_file():
                    file_path.unlink()
                    deleted_files += 1
            except Exception as e:
                print(f"Ошибка удаления файла {doc['file_path']}: {e}")
        
        # Удаляем записи из upload_logs
        doc_ids_internal = [doc['id'] for doc in internal_docs]
        doc_ids_external = [doc['id'] for doc in external_docs]
        
        if doc_ids_internal:
            placeholders = ','.join(['?'] * len(doc_ids_internal))
            cursor.execute(f"""
                DELETE FROM upload_logs 
                WHERE document_id IN ({placeholders}) AND category = 'internal'
            """, doc_ids_internal)
        
        if doc_ids_external:
            placeholders = ','.join(['?'] * len(doc_ids_external))
            cursor.execute(f"""
                DELETE FROM upload_logs 
                WHERE document_id IN ({placeholders}) AND category = 'external'
            """, doc_ids_external)
        
        # Удаляем документы из БД
        if doc_ids_internal:
            placeholders = ','.join(['?'] * len(doc_ids_internal))
            cursor.execute(f"DELETE FROM internal_documents WHERE id IN ({placeholders})", doc_ids_internal)
        
        if doc_ids_external:
            placeholders = ','.join(['?'] * len(doc_ids_external))
            cursor.execute(f"DELETE FROM external_documents WHERE id IN ({placeholders})", doc_ids_external)
        
        # Удаляем директории отдела из файловой системы
        storage_internal = BASE_DIR / 'storage' / 'internal'
        storage_external = BASE_DIR / 'storage' / 'external'
        
        # Функция для безопасного удаления директории
        def safe_remove_dir(dir_path):
            try:
                if dir_path.exists() and dir_path.is_dir():
                    shutil.rmtree(dir_path)
                    return True
            except Exception as e:
                print(f"Ошибка удаления директории {dir_path}: {e}")
            return False
        
        # Удаляем директорию отдела из internal
        dept_dir_internal = storage_internal / dept_name
        if dept_dir_internal.exists():
            safe_remove_dir(dept_dir_internal)
        
        # Удаляем директорию отдела из external
        dept_dir_external = storage_external / dept_name
        if dept_dir_external.exists():
            safe_remove_dir(dept_dir_external)
        
        # Обновляем ссылки на отдел у пользователей (устанавливаем NULL)
        cursor.execute("UPDATE users SET department_id = NULL WHERE department_id = ?", (dept_id,))
        
        # Удаляем сам отдел
        cursor.execute("DELETE FROM departments WHERE id = ?", (dept_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Отдел удален. Удалено документов: {len(all_docs)}, файлов: {deleted_files}'
        }), 200
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Ошибка удаления отдела: {error_trace}")
        return jsonify({
            'success': False,
            'message': f'Ошибка удаления отдела: {str(e)}'
        }), 500


@admin_bp.route('/documents', methods=['GET'])
@admin_required
def get_all_documents_admin(current_user):
    """Получение всех документов системы"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Внутренние документы
        cursor.execute("""
            SELECT d.id, d.title as name, d.file_name, d.file_size, d.created_at,
                   dt.name as type_name, dept.name as department_name, 
                   u.full_name as author_name, 'internal' as category
            FROM internal_documents d
            LEFT JOIN document_types dt ON d.document_type_id = dt.id
            LEFT JOIN departments dept ON d.department_id = dept.id
            LEFT JOIN users u ON d.author_id = u.id
            WHERE d.status != 'deleted'
            ORDER BY d.created_at DESC
        """)
        
        internal_docs = []
        for row in cursor.fetchall():
            internal_docs.append({
                'id': row['id'],
                'name': row['name'] or row['file_name'],
                'type_name': row['type_name'] or 'Без типа',
                'department_name': row['department_name'] or 'Без отдела',
                'author_name': row['author_name'] or 'Неизвестно',
                'file_size': row['file_size'],
                'created_at': row['created_at'],
                'category': 'internal'
            })
        
        # Внешние документы
        cursor.execute("""
            SELECT d.id, d.title as name, d.file_name, d.file_size, d.created_at,
                   dt.name as type_name, dept.name as department_name,
                   d.sender_name as author_name, 'external' as category
            FROM external_documents d
            LEFT JOIN document_types dt ON d.document_type_id = dt.id
            LEFT JOIN departments dept ON d.recipient_department_id = dept.id
            WHERE d.status != 'deleted'
            ORDER BY d.created_at DESC
        """)
        
        external_docs = []
        for row in cursor.fetchall():
            external_docs.append({
                'id': row['id'],
                'name': row['name'] or row['file_name'],
                'type_name': row['type_name'] or 'Без типа',
                'department_name': row['department_name'] or 'Без отдела',
                'author_name': row['author_name'] or 'Внешний отправитель',
                'file_size': row['file_size'],
                'created_at': row['created_at'],
                'category': 'external'
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'documents': internal_docs + external_docs
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@admin_bp.route('/system-stats', methods=['GET'])
@admin_required
def get_system_stats(current_user):
    """Получение системной статистики"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Общее количество документов
        cursor.execute("SELECT COUNT(*) FROM internal_documents WHERE status != 'deleted'")
        internal_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM external_documents WHERE status != 'deleted'")
        external_count = cursor.fetchone()[0]
        total_documents = internal_count + external_count
        
        # Количество пользователей
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        # Количество отделов
        cursor.execute("SELECT COUNT(*) FROM departments")
        total_departments = cursor.fetchone()[0]
        
        # Использование места (реально)
        import shutil
        storage_dir = BASE_DIR / 'storage'
        storage_usage = 0
        if storage_dir.exists():
            for file_path in storage_dir.rglob('*'):
                if file_path.is_file():
                    storage_usage += file_path.stat().st_size
        
        storage_usage_mb = storage_usage / (1024 * 1024)
        storage_usage_gb = storage_usage / (1024 * 1024 * 1024)
        
        # Получаем размер диска, на котором находится хранилище
        disk_usage = shutil.disk_usage(storage_dir if storage_dir.exists() else BASE_DIR)
        disk_total_gb = disk_usage.total / (1024 * 1024 * 1024)
        disk_free_gb = disk_usage.free / (1024 * 1024 * 1024)
        disk_used_gb = disk_usage.used / (1024 * 1024 * 1024)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_documents': total_documents,
                'total_users': total_users,
                'total_departments': total_departments,
                'storage_usage': f'{storage_usage_gb:.2f} GB',
                'storage_usage_mb': storage_usage_mb,
                'storage_usage_gb': storage_usage_gb,
                'disk_total_gb': disk_total_gb,
                'disk_free_gb': disk_free_gb,
                'disk_used_gb': disk_used_gb
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@admin_bp.route('/sync-files', methods=['POST'])
@admin_required
def sync_file_system(current_user):
    """Синхронизация файловой системы с БД"""
    try:
        # Простая проверка - находим файлы без записей в БД
        conn = get_db_connection()
        cursor = conn.cursor()
        
        missing_files = []
        
        # Проверяем внутренние документы
        cursor.execute("SELECT file_path FROM internal_documents WHERE status != 'deleted'")
        for row in cursor.fetchall():
            file_path = BASE_DIR / 'storage' / row['file_path']
            if not file_path.exists():
                missing_files.append(str(row['file_path']))
        
        # Проверяем внешние документы
        cursor.execute("SELECT file_path FROM external_documents WHERE status != 'deleted'")
        for row in cursor.fetchall():
            file_path = BASE_DIR / 'storage' / row['file_path']
            if not file_path.exists():
                missing_files.append(str(row['file_path']))
        
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Синхронизация завершена',
            'missing_files': missing_files
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@admin_bp.route('/backup', methods=['POST'])
@admin_required
def backup_database(current_user):
    """Создание резервной копии БД и файловой системы"""
    try:
        backup_dir = BASE_DIR / 'backups'
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_archive = backup_dir / f'backup_{timestamp}.zip'
        
        # Создаем ZIP архив
        with zipfile.ZipFile(backup_archive, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Добавляем базу данных
            zipf.write(DATABASE_PATH, 'database.db')
            
            # Добавляем файловую систему (storage)
            storage_dir = BASE_DIR / 'storage'
            if storage_dir.exists():
                for file_path in storage_dir.rglob('*'):
                    if file_path.is_file():
                        # Сохраняем относительный путь от storage
                        arcname = 'storage' / file_path.relative_to(storage_dir)
                        zipf.write(file_path, arcname)
        
        return jsonify({
            'success': True,
            'message': f'Резервная копия создана: {backup_archive.name}',
            'backup_file': str(backup_archive.name)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@admin_bp.route('/clear-notifications', methods=['POST'])
@admin_required
def clear_notifications(current_user):
    """Очистка прочитанных уведомлений"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM notifications WHERE is_read = 1")
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Удалено уведомлений: {deleted_count}'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

