"""
Сервис проверки прав доступа
"""
from backend.models.user import User


def can_view_document(user: User, document):
    """
    Проверяет, может ли пользователь просматривать документ
    
    Args:
        user: Объект User
        document: Объект Document
        
    Returns:
        bool: True если доступ разрешен
    """
    if not user:
        return False
    
    # Внешние документы доступны всем (определяем по наличию sender_name)
    if hasattr(document, 'sender_name'):
        return True
    
    # Администратор видит все
    if user.role == 'admin':
        return True
    
    # Руководитель отдела видит документы своего отдела
    if user.role == 'manager':
        if hasattr(document, 'department_id') and document.department_id == user.department_id:
            return True
        if hasattr(document, 'recipient_department_id') and document.recipient_department_id == user.department_id:
            return True
    
    # Обычный сотрудник видит:
    # - Документы своего отдела (включая других пользователей того же ранга)
    # - Документы, созданные им
    # - Документы, адресованные ему
    if user.role == 'user':
        # Документы отдела (все пользователи отдела видят документы друг друга)
        if hasattr(document, 'department_id') and document.department_id == user.department_id:
            return True
        if hasattr(document, 'recipient_department_id') and document.recipient_department_id == user.department_id:
            return True
        
        # Документы, созданные пользователем
        if hasattr(document, 'author_id') and document.author_id == user.id:
            return True
        
        # Документы, адресованные пользователю
        if hasattr(document, 'recipient_user_id') and document.recipient_user_id == user.id:
            return True
    
    return False


def can_edit_document(user: User, document):
    """
    Проверяет, может ли пользователь редактировать документ
    
    Args:
        user: Объект User
        document: Объект Document
        
    Returns:
        bool: True если доступ разрешен
    """
    if not user:
        return False
    
    # Администратор может редактировать все
    if user.role == 'admin':
        return True
    
    # Руководитель отдела может редактировать документы своего отдела
    if user.role == 'manager':
        if hasattr(document, 'department_id') and document.department_id == user.department_id:
            return True
    
    # Обычный сотрудник может редактировать документы своего отдела
    if user.role == 'user':
        if hasattr(document, 'department_id') and document.department_id == user.department_id:
            return True
    
    return False


def can_delete_document(user: User, document):
    """
    Проверяет, может ли пользователь удалять документ
    
    Args:
        user: Объект User
        document: Объект Document
        
    Returns:
        bool: True если доступ разрешен
    """
    # Только администратор может удалять
    return user and user.role == 'admin'

