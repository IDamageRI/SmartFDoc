"""
Сервис проверки сроков документов
"""
from datetime import datetime, timedelta
from backend.utils.db import get_db_connection
from backend.models.document import Document
from backend.services.notifications import notify_expiry_warning
from backend.config import EXPIRY_WARNING_DAYS


def check_expiring_documents():
    """
    Проверяет документы с истекающими сроками и создает уведомления
    
    Вызывается планировщиком (cron job или APScheduler)
    """
    today = datetime.now().date()
    warnings_created = 0
    
    # Проверяем для каждого дня предупреждения
    for days in EXPIRY_WARNING_DAYS:
        expiry_date = today + timedelta(days=days)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Проверяем внутренние документы
            cursor.execute("""
                SELECT * FROM internal_documents
                WHERE expiry_date = ?
                AND status = 'active'
            """, (expiry_date,))
            
            rows = cursor.fetchall()
            for row in rows:
                doc = Document.from_row(row, 'internal_documents')
                
                # Получаем пользователей, которым нужно отправить уведомление
                # Автор документа и получатели
                users_to_notify = []
                
                if hasattr(doc, 'author_id') and doc.author_id:
                    users_to_notify.append(doc.author_id)
                
                if hasattr(doc, 'recipient_user_id') and doc.recipient_user_id:
                    if doc.recipient_user_id not in users_to_notify:
                        users_to_notify.append(doc.recipient_user_id)
                
                # Если есть отдел-получатель, уведомляем всех в отделе
                if hasattr(doc, 'recipient_department_id') and doc.recipient_department_id:
                    cursor.execute("""
                        SELECT id FROM users 
                        WHERE department_id = ?
                    """, (doc.recipient_department_id,))
                    dept_users = cursor.fetchall()
                    for user_row in dept_users:
                        if user_row['id'] not in users_to_notify:
                            users_to_notify.append(user_row['id'])
                
                # Создаем уведомления
                for user_id in users_to_notify:
                    notify_expiry_warning(user_id, doc, days, 'internal_documents')
                    warnings_created += 1
            
            # Проверяем внешние документы
            cursor.execute("""
                SELECT * FROM external_documents
                WHERE expiry_date = ?
                AND status = 'active'
            """, (expiry_date,))
            
            rows = cursor.fetchall()
            for row in rows:
                doc = Document.from_row(row, 'external_documents')
                
                users_to_notify = []
                
                if hasattr(doc, 'recipient_user_id') and doc.recipient_user_id:
                    users_to_notify.append(doc.recipient_user_id)
                
                if hasattr(doc, 'recipient_department_id') and doc.recipient_department_id:
                    cursor.execute("""
                        SELECT id FROM users 
                        WHERE department_id = ?
                    """, (doc.recipient_department_id,))
                    dept_users = cursor.fetchall()
                    for user_row in dept_users:
                        if user_row['id'] not in users_to_notify:
                            users_to_notify.append(user_row['id'])
                
                for user_id in users_to_notify:
                    notify_expiry_warning(user_id, doc, days, 'external_documents')
                    warnings_created += 1
        
        finally:
            conn.close()
    
    return warnings_created


def run_expiry_check():
    """Запускает проверку сроков (для использования в планировщике)"""
    try:
        count = check_expiring_documents()
        print(f"✓ Проверка сроков выполнена. Создано уведомлений: {count}")
        return count
    except Exception as e:
        print(f"❌ Ошибка при проверке сроков: {e}")
        return 0

