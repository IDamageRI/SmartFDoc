from flask import Blueprint, request, jsonify
from backend.utils.middleware import login_required
from backend.services.mail_loader import MailLoader
from backend.utils.db import get_db_connection
from datetime import datetime

mail_bp = Blueprint('mail', __name__, url_prefix='/api/mail')


@mail_bp.route('/download', methods=['POST'])
@login_required
def download_from_mail(current_user):
    """Загружает документы с почты"""
    try:
        data = request.get_json()
        email_address = data.get('email')
        password = data.get('password')
        server = data.get('server', 'imap.yandex.ru')
        
        if not email_address or not password:
            return jsonify({
                'success': False,
                'error': {'message': 'Не указаны email или пароль'}
            }), 400
        
        loader = MailLoader(server, email_address, password)
        
        if not loader.connect():
            return jsonify({
                'success': False,
                'error': {'message': 'Ошибка подключения к почте'}
            }), 400
        
        documents = loader.download_and_process_files()
        loader.disconnect()
        
        if not documents:
            return jsonify({
                'success': True,
                'message': 'Новых документов не найдено',
                'documents_count': 0
            }), 200
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        created_count = 0
        
        for doc_data in documents:
            try:
                department_id = None
                if doc_data['department_name']:
                    cursor.execute("SELECT id FROM departments WHERE name = ?", (doc_data['department_name'],))
                    dept_row = cursor.fetchone()
                    if dept_row:
                        department_id = dept_row['id']
                
                cursor.execute("""
                    INSERT INTO external_documents 
                    (document_type_id, title, description, file_path, file_name, 
                     file_size, file_extension, sender_name, sender_email, sender_contact, sender_inn, sender_kpp,
                     recipient_department_id, recipient_user_id, document_date, received_date, expiry_date,
                     work_status, completion_percent)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc_data['document_type_id'],
                    doc_data['title'],
                    f"Загружено с почты {email_address}",
                    doc_data['file_path'],
                    doc_data['file_name'],
                    doc_data['file_size'],
                    doc_data['file_extension'],
                    doc_data['sender_name'],
                    doc_data.get('sender_email'),
                    email_address,
                    doc_data.get('sender_inn'),
                    doc_data.get('sender_kpp'),
                    department_id,
                    current_user.id,
                    doc_data['document_date'],
                    datetime.now().date().isoformat(),
                    None,
                    'not_processed',
                    0
                ))
                
                doc_id = cursor.lastrowid
                
                try:
                    cursor.execute("""
                        INSERT INTO upload_logs (document_id, category, user_id)
                        VALUES (?, ?, ?)
                    """, (doc_id, 'external', current_user.id))
                except:
                    pass
                
                created_count += 1
            except Exception as e:
                print(f"Ошибка сохранения документа {doc_data['file_name']}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Загружено документов: {created_count}',
            'documents_count': created_count
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500

