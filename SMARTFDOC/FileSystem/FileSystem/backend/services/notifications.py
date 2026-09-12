from backend.models.notification import Notification
from backend.models.user import User
from backend.models.document import Document


def notify_document_received(user_id, document, document_table='internal_documents'):
    title = f"Получен новый документ: {document.title}"
    message = f"Документ '{document.title}' был отправлен вам"
    
    Notification.create(
        user_id=user_id,
        type='document_received',
        title=title,
        message=message,
        document_id=document.id,
        document_table=document_table
    )


def notify_document_sent(user_id, document, document_table='internal_documents'):
    title = f"Документ успешно загружен: {document.title}"
    message = f"Документ '{document.title}' был успешно загружен в систему"
    
    Notification.create(
        user_id=user_id,
        type='document_sent',
        title=title,
        message=message,
        document_id=document.id,
        document_table=document_table
    )


def notify_department_document(user_id, document, document_table='internal_documents'):
    title = f"Новый документ в отделе: {document.title}"
    message = f"В вашем отделе появился новый документ '{document.title}'"
    
    Notification.create(
        user_id=user_id,
        type='document_received',
        title=title,
        message=message,
        document_id=document.id,
        document_table=document_table
    )


def notify_expiry_warning(user_id, document, days_left, document_table='internal_documents'):
    title = f"Срок документа истекает: {document.title}"
    message = f"Документ '{document.title}' истекает через {days_left} дн."
    
    Notification.create(
        user_id=user_id,
        type='expiry_warning',
        title=title,
        message=message,
        document_id=document.id,
        document_table=document_table
    )


def create_duplicate_notification(user_id, filename, duplicates):
    try:
        from backend.utils.db import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        duplicate_info = "\n".join([
            f"- {doc['title']} (ID: {doc['id']}, от {doc.get('document_date', 'неизвестно')})"
            for doc in duplicates[:3]
        ])
        
        if len(duplicates) > 3:
            duplicate_info += f"\n- ... и еще {len(duplicates) - 3} дубликат(ов)"
        
        message = f"""Попытка загрузки дубликата файла: {filename}

Найдены существующие копии:
{duplicate_info}

Рекомендуется проверить необходимость загрузки этого файла."""
        
        cursor.execute("""
            INSERT INTO notifications 
            (user_id, type, title, message, is_read, created_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, 'duplicate_upload', f'Дубликат файла: {filename}', message, 0))
        
        conn.commit()
        conn.close()
    except Exception as e:
        pass


def create_duplicate_report_notification(duplicates):
    try:
        from backend.utils.db import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM users WHERE role = 'admin'")
        admins = cursor.fetchall()
        
        total_duplicates = sum(len(group) for group in duplicates)
        
        for admin in admins:
            message = f"""В системе обнаружены дубликаты документов.

Всего групп дубликатов: {len(duplicates)}
Общее количество дубликатов: {total_duplicates}

Рекомендуется проверить раздел "Дубликаты документов" для разрешения конфликтов."""
            
            cursor.execute("""
                INSERT INTO notifications 
                (user_id, type, title, message, is_read, created_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (admin['id'], 'duplicate_report', 'Обнаружены дубликаты документов', message, 0))
        
        conn.commit()
        conn.close()
    except Exception as e:
        pass


def create_document_notifications(document, document_table, author_id):
    try:
        from backend.utils.db import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if document_table == 'internal_documents':
            if hasattr(document, 'recipient_user_id') and document.recipient_user_id:
                notify_document_received(document.recipient_user_id, document, document_table)
            
            if hasattr(document, 'recipient_department_id') and document.recipient_department_id:
                cursor.execute("""
                    SELECT id FROM users 
                    WHERE department_id = ? AND id != ?
                """, (document.recipient_department_id, author_id))
                
                dept_users = cursor.fetchall()
                for user in dept_users:
                    notify_department_document(user['id'], document, document_table)
            
            if hasattr(document, 'department_id') and document.department_id:
                cursor.execute("""
                    SELECT id FROM users 
                    WHERE department_id = ? AND id != ?
                """, (document.department_id, author_id))
                
                dept_users = cursor.fetchall()
                for user in dept_users:
                    notify_department_document(user['id'], document, document_table)
        
        elif document_table == 'external_documents':
            if hasattr(document, 'recipient_user_id') and document.recipient_user_id:
                notify_document_received(document.recipient_user_id, document, document_table)
            
            if hasattr(document, 'recipient_department_id') and document.recipient_department_id:
                cursor.execute("""
                    SELECT id FROM users 
                    WHERE department_id = ? AND id != ?
                """, (document.recipient_department_id, author_id))
                
                dept_users = cursor.fetchall()
                for user in dept_users:
                    notify_department_document(user['id'], document, document_table)
        
        notify_document_sent(author_id, document, document_table)
        conn.close()
    except Exception as e:
        pass
