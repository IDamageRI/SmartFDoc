"""
Модель типа документа
"""
from backend.utils.db import get_db_connection


class DocumentType:
    """Модель типа документа"""
    
    def __init__(self, id=None, name=None, description=None, category=None, created_at=None):
        self.id = id
        self.name = name
        self.description = description
        self.category = category
        self.created_at = created_at
    
    @classmethod
    def from_row(cls, row):
        """Создает объект DocumentType из строки БД"""
        if not row:
            return None
        
        return cls(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            category=row['category'],
            created_at=row['created_at']
        )
    
    @classmethod
    def get_all(cls):
        """Получает все типы документов"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM document_types ORDER BY name")
            rows = cursor.fetchall()
            return [cls.from_row(row) for row in rows]
        finally:
            conn.close()
    
    @classmethod
    def find_by_id(cls, type_id):
        """Находит тип документа по ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT * FROM document_types WHERE id = ?",
                (type_id,)
            )
            row = cursor.fetchone()
            return cls.from_row(row)
        finally:
            conn.close()
    
    def to_dict(self):
        """Преобразует объект в словарь"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'created_at': self.created_at
        }

