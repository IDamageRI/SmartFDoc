import hashlib
import os
from pathlib import Path
from datetime import datetime
from backend.utils.db import get_db_connection
from backend.config import STORAGE_INTERNAL, STORAGE_EXTERNAL, BASE_DIR


class DuplicateDetector:
    
    def __init__(self):
        self.duplicates = []
    
    def find_duplicates(self, method='hash', category=None, department_id=None):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            documents = []
            
            if category is None or category == 'internal':
                cursor.execute("""
                    SELECT id, document_type_id, title, file_path, file_name, file_size, 
                        file_extension, department_id, author_id, document_date, expiry_date,
                        'internal' as category
                    FROM internal_documents 
                    WHERE status = 'active'
                """)
                internal_docs = cursor.fetchall()
                for row in internal_docs:
                    documents.append(dict(row))
            
            if category is None or category == 'external':
                cursor.execute("""
                    SELECT id, document_type_id, title, file_path, file_name, file_size, 
                        file_extension, recipient_department_id as department_id, 
                        NULL as author_id, document_date, expiry_date,
                        'external' as category
                    FROM external_documents 
                    WHERE status = 'active'
                """)
                external_docs = cursor.fetchall()
                for row in external_docs:
                    documents.append(dict(row))
            
            conn.close()
            
            if method == 'hash':
                return self._find_duplicates_by_hash(documents)
            elif method == 'filename':
                return self._find_duplicates_by_filename(documents)
            elif method == 'metadata':
                return self._find_duplicates_by_metadata(documents)
            else:
                return []
                
        except Exception as e:
            print(f"Ошибка поиска дубликатов: {e}")
            return []
    
    def _find_duplicates_by_hash(self, documents):
        hash_groups = {}
        
        for doc in documents:
            try:
                file_path = BASE_DIR / doc['file_path']
                if not file_path.exists():
                    continue
                
                file_hash = self._calculate_file_hash(file_path)
                
                if file_hash not in hash_groups:
                    hash_groups[file_hash] = []
                
                hash_groups[file_hash].append({
                    'id': doc['id'],
                    'title': doc['title'],
                    'file_name': doc['file_name'],
                    'file_path': doc['file_path'],
                    'file_size': doc['file_size'],
                    'category': doc['category'],
                    'document_date': doc['document_date'],
                    'hash': file_hash
                })
                
            except Exception as e:
                print(f"Ошибка обработки файла {doc['file_path']}: {e}")
                continue
        
        return [group for group in hash_groups.values() if len(group) > 1]
    
    def _find_duplicates_by_filename(self, documents):
        filename_groups = {}
        
        for doc in documents:
            filename = doc['file_name'].lower().strip()
            
            if filename not in filename_groups:
                filename_groups[filename] = []
            
            filename_groups[filename].append({
                'id': doc['id'],
                'title': doc['title'],
                'file_name': doc['file_name'],
                'file_path': doc['file_path'],
                'file_size': doc['file_size'],
                'category': doc['category'],
                'document_date': doc['document_date']
            })
        
        return [group for group in filename_groups.values() if len(group) > 1]
    
    def _find_duplicates_by_metadata(self, documents):
        metadata_groups = {}
        
        for doc in documents:
            key = f"{doc['title'].lower().strip()}_{doc['file_size']}_{doc['document_date']}"
            
            if key not in metadata_groups:
                metadata_groups[key] = []
            
            metadata_groups[key].append({
                'id': doc['id'],
                'title': doc['title'],
                'file_name': doc['file_name'],
                'file_path': doc['file_path'],
                'file_size': doc['file_size'],
                'category': doc['category'],
                'document_date': doc['document_date']
            })
        
        return [group for group in metadata_groups.values() if len(group) > 1]
    
    def _calculate_file_hash(self, file_path, chunk_size=8192):
        hash_md5 = hashlib.md5()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hash_md5.update(chunk)
        
        return hash_md5.hexdigest()
    
    def get_duplicates_report(self, duplicates):
        report = {
            'total_groups': len(duplicates),
            'total_duplicates': sum(len(group) for group in duplicates),
            'groups': []
        }
        
        for i, group in enumerate(duplicates):
            group_info = {
                'group_id': i + 1,
                'count': len(group),
                'documents': group,
                'primary_document': self._select_primary_document(group)
            }
            report['groups'].append(group_info)
        
        return report
    
    def _select_primary_document(self, documents):
        if not documents:
            return None
        
        return sorted(documents, key=lambda x: x.get('document_date', ''), reverse=True)[0]

    def check_duplicate_before_upload(self, file, metadata, target_file_path):
        try:
            target_dir = target_file_path.parent
            target_filename = target_file_path.name
            target_filename_lower = target_filename.lower()
            
            if target_file_path.exists():
                return {
                    'is_duplicate': True,
                    'duplicates': [{
                        'id': None,
                        'title': target_filename,
                        'file_name': target_filename,
                        'file_path': str(target_file_path.relative_to(BASE_DIR)),
                        'document_date': None,
                        'message': f'Файл с именем "{target_filename}" уже существует в этой папке'
                    }],
                    'message': f'Файл с именем "{target_filename}" уже существует в папке {target_dir.relative_to(BASE_DIR)}'
                }
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            duplicates = []
            relative_path = str(target_file_path.relative_to(BASE_DIR))
            relative_dir = str(target_dir.relative_to(BASE_DIR))
            
            cursor.execute("""
                SELECT id, title, file_name, file_path, file_size, 
                    department_id, author_id, document_date,
                    'internal' as category
                FROM internal_documents 
                WHERE status = 'active' AND file_path = ?
            """, (relative_path,))
            internal_dups = cursor.fetchall()
            
            cursor.execute("""
                SELECT id, title, file_name, file_path, file_size, 
                    recipient_department_id as department_id,
                    NULL as author_id, document_date,
                    'external' as category
                FROM external_documents 
                WHERE status = 'active' AND file_path = ?
            """, (relative_path,))
            external_dups = cursor.fetchall()
            
            for row in internal_dups + external_dups:
                duplicates.append(dict(row))
            
            if not duplicates:
                cursor.execute("""
                    SELECT id, title, file_name, file_path, file_size, 
                        department_id, author_id, document_date,
                        'internal' as category
                    FROM internal_documents 
                    WHERE status = 'active' 
                    AND LOWER(file_name) = ?
                    AND file_path LIKE ?
                """, (target_filename_lower, f'{relative_dir}%'))
                internal_name_dups = cursor.fetchall()
                
                cursor.execute("""
                    SELECT id, title, file_name, file_path, file_size, 
                        recipient_department_id as department_id,
                        NULL as author_id, document_date,
                        'external' as category
                    FROM external_documents 
                    WHERE status = 'active' 
                    AND LOWER(file_name) = ?
                    AND file_path LIKE ?
                """, (target_filename_lower, f'{relative_dir}%'))
                external_name_dups = cursor.fetchall()
                
                for row in internal_name_dups + external_name_dups:
                    duplicates.append(dict(row))
            
            conn.close()
            
            if duplicates:
                return {
                    'is_duplicate': True,
                    'duplicates': duplicates,
                    'message': f'Найдено {len(duplicates)} документ(ов) с таким же именем файла в этой папке'
                }
            
            return {
                'is_duplicate': False,
                'duplicates': [],
                'message': 'Дубликатов не найдено'
            }
            
        except Exception as e:
            print(f"Ошибка проверки дубликатов: {e}")
            return {
                'is_duplicate': False,
                'duplicates': [],
                'message': f'Ошибка проверки: {str(e)}'
            }


duplicate_detector = DuplicateDetector()