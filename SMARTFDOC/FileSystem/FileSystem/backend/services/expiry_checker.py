from datetime import datetime, timedelta
from backend.utils.db import get_db_connection
from backend.models.document import Document
from backend.services.notifications import notify_expiry_warning
from backend.config import EXPIRY_WARNING_DAYS


def check_expiring_documents():
    today = datetime.now().date()
    warnings_created = 0
    
    for days in EXPIRY_WARNING_DAYS:
        expiry_date = today + timedelta(days=days)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM internal_documents
                WHERE expiry_date = ?
                AND status = 'active'
            """, (expiry_date,))
            
            internal_docs = cursor.fetchall()
            
            for row in internal_docs:
                doc = Document.from_row(row, 'internal_documents')
                
                if hasattr(doc, 'department_id') and doc.department_id:
                    cursor.execute("""
                        SELECT id FROM users 
                        WHERE department_id = ?
                    """, (doc.department_id,))
                    
                    users = cursor.fetchall()
                    for user in users:
                        notify_expiry_warning(user['id'], doc, days, 'internal_documents')
                        warnings_created += 1
            
            cursor.execute("""
                SELECT * FROM external_documents
                WHERE expiry_date = ?
                AND status = 'active'
            """, (expiry_date,))
            
            external_docs = cursor.fetchall()
            
            for row in external_docs:
                doc = Document.from_row(row, 'external_documents')
                
                if hasattr(doc, 'recipient_department_id') and doc.recipient_department_id:
                    cursor.execute("""
                        SELECT id FROM users 
                        WHERE department_id = ?
                    """, (doc.recipient_department_id,))
                    
                    users = cursor.fetchall()
                    for user in users:
                        notify_expiry_warning(user['id'], doc, days, 'external_documents')
                        warnings_created += 1
        finally:
            conn.close()
    
    return warnings_created


def run_expiry_check():
    try:
        count = check_expiring_documents()
        print(f"✓ Проверка сроков выполнена. Создано уведомлений: {count}")
        return count
    except Exception as e:
        print(f"❌ Ошибка при проверке сроков: {e}")
        return 0
