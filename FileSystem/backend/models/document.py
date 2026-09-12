from backend.utils.db import get_db_connection
from datetime import datetime


class Document:
    
    def __init__(self, id=None, document_type_id=None, title=None, description=None,
                 file_path=None, file_name=None, file_size=None, file_extension=None,
                 document_date=None, created_at=None, updated_at=None, status='active',
                 expiry_date=None, work_status='not_processed', completion_percent=0):
        self.id = id
        self.document_type_id = document_type_id
        self.title = title
        self.description = description
        self.file_path = file_path
        self.file_name = file_name
        self.file_size = file_size
        self.file_extension = file_extension
        self.document_date = document_date
        self.expiry_date = expiry_date
        self.work_status = work_status
        self.completion_percent = completion_percent
        self.created_at = created_at
        self.updated_at = updated_at
        self.status = status
    
    @classmethod
    def from_row(cls, row, table_name='internal_documents'):
        if not row:
            return None
        
        def safe_get(key, default=None):
            return row[key] if key in row.keys() else default
        
        doc = cls(
            id=row['id'],
            document_type_id=safe_get('document_type_id'),
            title=row['title'],
            description=safe_get('description'),
            file_path=row['file_path'],
            file_name=row['file_name'],
            file_size=safe_get('file_size'),
            file_extension=safe_get('file_extension'),
            document_date=safe_get('document_date'),
            created_at=row['created_at'],
            updated_at=safe_get('updated_at'),
            status=safe_get('status', 'active')
        )
        doc.expiry_date = safe_get('expiry_date')
        doc.work_status = safe_get('work_status', 'not_processed')
        doc.completion_percent = safe_get('completion_percent', 0)
        
        if table_name == 'internal_documents':
            doc.department_id = safe_get('department_id')
            doc.author_id = safe_get('author_id')
            doc.recipient_department_id = safe_get('recipient_department_id')
            doc.recipient_user_id = safe_get('recipient_user_id')
        elif table_name == 'external_documents':
            doc.sender_name = safe_get('sender_name')
            doc.sender_contact = safe_get('sender_contact')
            doc.recipient_department_id = safe_get('recipient_department_id')
            doc.recipient_user_id = safe_get('recipient_user_id')
            doc.received_date = safe_get('received_date')
        
        return doc
    
    def to_dict(self, include_relations=False):
        data = {
            'id': self.id,
            'document_type_id': self.document_type_id,
            'title': self.title,
            'description': self.description,
            'file_path': self.file_path,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'file_extension': self.file_extension,
            'document_date': self.document_date,
            'expiry_date': self.expiry_date,
            'work_status': getattr(self, 'work_status', 'not_processed'),
            'completion_percent': getattr(self, 'completion_percent', 0),
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'status': self.status
        }
        
        if hasattr(self, 'department_id'):
            data['department_id'] = self.department_id
        if hasattr(self, 'author_id'):
            data['author_id'] = self.author_id
        if hasattr(self, 'sender_name'):
            data['sender_name'] = self.sender_name
        if hasattr(self, 'sender_contact'):
            data['sender_contact'] = self.sender_contact
        
        return data

