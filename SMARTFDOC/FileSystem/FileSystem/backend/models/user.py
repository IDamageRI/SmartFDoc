from backend.utils.db import get_db_connection
from backend.utils.validators import hash_password, check_password


class User:
    
    def __init__(self, id=None, username=None, full_name=None, email=None, 
                 department_id=None, role=None, password_hash=None, 
                 created_at=None, updated_at=None):
        self.id = id
        self.username = username
        self.full_name = full_name
        self.email = email
        self.department_id = department_id
        self.role = role
        self.password_hash = password_hash
        self.created_at = created_at
        self.updated_at = updated_at
    
    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        
        password_hash = row['password_hash'] if 'password_hash' in row.keys() else None
        
        return cls(
            id=row['id'],
            username=row['username'],
            full_name=row['full_name'],
            email=row['email'],
            department_id=row['department_id'],
            role=row['role'],
            password_hash=password_hash,
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
    
    @classmethod
    def find_by_username(cls, username):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()
            return cls.from_row(row)
        finally:
            conn.close()
    
    @classmethod
    def find_by_id(cls, user_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT * FROM users WHERE id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            return cls.from_row(row)
        finally:
            conn.close()
    
    def verify_password(self, password):
        return check_password(self.password_hash, password)
    
    def to_dict(self, include_password=False):
        data = {
            'id': self.id,
            'username': self.username,
            'full_name': self.full_name,
            'email': self.email,
            'department_id': self.department_id,
            'role': self.role,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        
        if include_password:
            data['password_hash'] = self.password_hash
        
        return data

