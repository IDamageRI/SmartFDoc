from backend.models.user import User


def can_view_document(user: User, document):
    if not user:
        return False
    
    if user.role == 'admin':
        return True
    
    if user.role == 'manager':
        return True
    
    if user.role == 'user':
        if hasattr(document, 'department_id') and document.department_id == user.department_id:
            return True
        if hasattr(document, 'recipient_department_id') and document.recipient_department_id == user.department_id:
            return True
        
        if hasattr(document, 'sender_name'):  # Внешний документ
            if hasattr(document, 'recipient_department_id') and document.recipient_department_id == user.department_id:
                return True
            return False
        
        if hasattr(document, 'author_id') and document.author_id == user.id:
            return True
        
        if hasattr(document, 'recipient_user_id') and document.recipient_user_id == user.id:
            return True
    
    return False


def can_edit_document(user: User, document):
    if not user:
        return False
    
    if user.role == 'admin':
        return True
    
    if user.role == 'manager':
        if hasattr(document, 'department_id') and document.department_id == user.department_id:
            return True
    
    if user.role == 'user':
        if hasattr(document, 'department_id') and document.department_id == user.department_id:
            return True
    
    return False


def can_delete_document(user: User, document):
    if not user:
        return False
    
    return user.role in ['admin', 'manager']

