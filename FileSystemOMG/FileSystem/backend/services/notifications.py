"""
Сервис создания уведомлений
"""
from backend.models.notification import Notification
from backend.models.user import User
from backend.models.document import Document


def notify_document_received(user_id, document, document_table='internal_documents'):
    """
    Создает уведомление о получении документа
    
    Args:
        user_id: ID пользователя-получателя
        document: Объект Document
        document_table: Таблица документа
    """
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
    """
    Создает уведомление об отправке документа
    
    Args:
        user_id: ID пользователя-отправителя
        document: Объект Document
        document_table: Таблица документа
    """
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
    """
    Создает уведомление для отдела о новом документе
    
    Args:
        user_id: ID пользователя из отдела
        document: Объект Document
        document_table: Таблица документа
    """
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
    """
    Создает уведомление о приближении срока истечения документа
    
    Args:
        user_id: ID пользователя
        document: Объект Document
        days_left: Количество дней до истечения
        document_table: Таблица документа
    """
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


def create_document_notifications(document, document_table='internal_documents', author_id=None):
    """
    Создает уведомления при создании документа
    
    Args:
        document: Объект Document
        document_table: Таблица документа
        author_id: ID автора документа
    """
    from backend.utils.db import get_db_connection
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Уведомление автору
        if author_id:
            notify_document_sent(author_id, document, document_table)
        
        # Уведомления получателям
        if hasattr(document, 'recipient_user_id') and document.recipient_user_id:
            notify_document_received(document.recipient_user_id, document, document_table)
        
        # Уведомления отделу-получателю
        if hasattr(document, 'recipient_department_id') and document.recipient_department_id:
            cursor.execute("""
                SELECT id FROM users 
                WHERE department_id = ? AND id != ?
            """, (document.recipient_department_id, author_id or 0))
            
            users = cursor.fetchall()
            for user_row in users:
                notify_department_document(user_row['id'], document, document_table)
        
        # Уведомления отделу документа (если не получатель)
        if hasattr(document, 'department_id') and document.department_id:
            if not hasattr(document, 'recipient_department_id') or document.department_id != document.recipient_department_id:
                cursor.execute("""
                    SELECT id FROM users 
                    WHERE department_id = ? AND id != ?
                """, (document.department_id, author_id or 0))
                
                users = cursor.fetchall()
                for user_row in users:
                    notify_department_document(user_row['id'], document, document_table)
    
    finally:
        conn.close()

