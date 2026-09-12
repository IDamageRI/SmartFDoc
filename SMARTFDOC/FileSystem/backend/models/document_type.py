from backend.utils.db import get_db_connection


class DocumentType:
    
    def __init__(self, id=None, name=None, description=None, category=None, created_at=None):
        self.id = id
        self.name = name
        self.description = description
        self.category = category
        self.created_at = created_at
    
    @classmethod
    def from_row(cls, row):
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
    
    @classmethod
    def find_by_name(cls, name):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT * FROM document_types WHERE name = ?",
                (name,)
            )
            row = cursor.fetchone()
            return cls.from_row(row)
        finally:
            conn.close()
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'created_at': self.created_at
        }

