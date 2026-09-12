"""
Модель уведомления
"""
from backend.utils.db import get_db_connection


class Notification:
    """Модель уведомления"""
    
    def __init__(self, id=None, user_id=None, type=None, title=None, message=None,
                 document_id=None, document_table=None, is_read=False, created_at=None):
        self.id = id
        self.user_id = user_id
        self.type = type
        self.title = title
        self.message = message
        self.document_id = document_id
        self.document_table = document_table
        self.is_read = is_read
        self.created_at = created_at
    
    @classmethod
    def from_row(cls, row):
        """Создает объект Notification из строки БД"""
        if not row:
            return None
        
        # sqlite3.Row не имеет метода .get(), используем проверку через keys()
        def safe_get(key, default=None):
            return row[key] if key in row.keys() else default
        
        return cls(
            id=row['id'],
            user_id=row['user_id'],
            type=row['type'],
            title=row['title'],
            message=safe_get('message'),
            document_id=safe_get('document_id'),
            document_table=safe_get('document_table'),
            is_read=bool(safe_get('is_read', 0)),
            created_at=row['created_at']
        )
    
    @classmethod
    def get_user_notifications(cls, user_id, unread_only=False):
        """Получает уведомления пользователя"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            if unread_only:
                cursor.execute("""
                    SELECT * FROM notifications 
                    WHERE user_id = ? AND is_read = 0
                    ORDER BY created_at DESC
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT * FROM notifications 
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                """, (user_id,))
            
            rows = cursor.fetchall()
            return [cls.from_row(row) for row in rows]
        finally:
            conn.close()
    
    @classmethod
    def get_unread_count(cls, user_id):
        """Получает количество непрочитанных уведомлений"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT COUNT(*) as count FROM notifications 
                WHERE user_id = ? AND is_read = 0
            """, (user_id,))
            row = cursor.fetchone()
            return row['count'] if row else 0
        finally:
            conn.close()
    
    @classmethod
    def create(cls, user_id, type, title, message=None, document_id=None, document_table=None):
        """Создает новое уведомление"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO notifications 
                (user_id, type, title, message, document_id, document_table)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, type, title, message, document_id, document_table))
            
            notification_id = cursor.lastrowid
            conn.commit()
            
            # Получаем созданное уведомление
            cursor.execute("SELECT * FROM notifications WHERE id = ?", (notification_id,))
            row = cursor.fetchone()
            return cls.from_row(row)
        finally:
            conn.close()
    
    def mark_as_read(self):
        """Отмечает уведомление как прочитанное"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE notifications SET is_read = 1 WHERE id = ?
            """, (self.id,))
            conn.commit()
            self.is_read = True
        finally:
            conn.close()
    
    def delete(self):
        """Удаляет уведомление"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM notifications WHERE id = ?", (self.id,))
            conn.commit()
        finally:
            conn.close()
    
    def to_dict(self):
        """Преобразует объект в словарь"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'document_id': self.document_id,
            'document_table': self.document_table,
            'is_read': self.is_read,
            'created_at': self.created_at
        }

