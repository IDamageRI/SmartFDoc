import re
import logging
from backend.utils.db import get_db_connection

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def apply_classification_rules(file, metadata):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='classification_rules'
        """)
        
        if not cursor.fetchone():
            conn.close()
            return metadata
        
        cursor.execute("""
            SELECT condition_text, action_text, priority
            FROM classification_rules
            WHERE is_active = 1
            ORDER BY priority DESC, created_at DESC
        """)
        
        rules = cursor.fetchall()
        conn.close()
        
        filename = file.filename if hasattr(file, 'filename') else str(file)
        
        logger.debug(f"Применение правил классификации для файла: {filename}, метаданные: {metadata}")
        
        for rule in rules:
            condition_text = rule['condition_text']
            action_text = rule['action_text']
            
            logger.debug(f"Проверка правила: {condition_text}")
            if evaluate_conditions(condition_text, filename, metadata):
                logger.debug(f"Правило сработало: {condition_text} -> {action_text}")
                metadata = apply_actions(action_text, metadata)
                logger.debug(f"Метаданные после применения: {metadata}")
            else:
                logger.debug(f"Правило не сработало: {condition_text}")
        
        logger.debug(f"Итоговые метаданные: {metadata}")
        return metadata
        
    except Exception as e:
        logger.error(f"Ошибка применения правил классификации: {e}")
        return metadata


def evaluate_conditions(condition_text, filename, metadata):
    try:
        condition_text = condition_text.strip()
        
        if ' ИЛИ ' in condition_text.upper() or ' OR ' in condition_text.upper():
            parts = re.split(r'\s+(?:ИЛИ|OR)\s+', condition_text, flags=re.IGNORECASE)
            return any(evaluate_condition(part.strip(), filename, metadata) for part in parts)
        
        elif ' И ' in condition_text.upper() or ' AND ' in condition_text.upper():
            parts = re.split(r'\s+(?:И|AND)\s+', condition_text, flags=re.IGNORECASE)
            return all(evaluate_condition(part.strip(), filename, metadata) for part in parts)
        
        else:
            return evaluate_condition(condition_text, filename, metadata)
            
    except Exception as e:
        logger.error(f"Ошибка оценки условий: {e}")
        return False


def evaluate_condition(condition, filename, metadata):
    try:
        condition = condition.strip().lower()
        filename_lower = filename.lower()
        
        if "имя файла содержит" in condition or "filename contains" in condition:
            match = re.search(r"['\"]([^'\"]+)['\"]", condition)
            if match:
                text = match.group(1).lower()
                return text in filename_lower
                
        elif "имя файла начинается с" in condition or "filename starts with" in condition:
            match = re.search(r"['\"]([^'\"]+)['\"]", condition)
            if match:
                text = match.group(1).lower()
                return filename_lower.startswith(text)
                
        elif "имя файла заканчивается на" in condition or "filename ends with" in condition:
            match = re.search(r"['\"]([^'\"]+)['\"]", condition)
            if match:
                text = match.group(1).lower()
                return filename_lower.endswith(text)
                
        elif "расширение" in condition or "extension" in condition:
            match = re.search(r"['\"]([^'\"]+)['\"]", condition)
            if match:
                ext = match.group(1).lower().lstrip('.')
                file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
                return ext == file_ext
                
        elif "категория" in condition or "category" in condition:
            match = re.search(r"['\"]([^'\"]+)['\"]", condition)
            if match:
                cat = match.group(1).lower()
                current_cat = metadata.get('category', '').lower()
                return cat == current_cat
        
        else:
            text = condition.strip().strip('"').strip("'")
            if text and len(text) > 0:
                return text in filename_lower
                
        return False
        
    except Exception as e:
        logger.error(f"Ошибка оценки условия '{condition}': {e}")
        return False


def apply_actions(action_text, metadata):
    try:
        actions = [a.strip() for a in action_text.split(';') if a.strip()]
        
        for action in actions:
            metadata = apply_action(action, metadata)
        
        return metadata
        
    except Exception as e:
        logger.error(f"Ошибка применения действий: {e}")
        return metadata


def apply_action(action, metadata):
    try:
        action = action.strip()
        
        if "присвоить тип" in action.lower() or "assign type" in action.lower():
            match = re.search(r"['\"]([^'\"]+)['\"]", action)
            if match:
                type_name = match.group(1)
                from backend.models.document_type import DocumentType
                doc_type = DocumentType.find_by_name(type_name)
                if doc_type:
                    metadata['document_type_id'] = doc_type.id
                    
        elif "присвоить категорию" in action.lower() or "assign category" in action.lower():
            match = re.search(r"['\"]([^'\"]+)['\"]", action)
            if match:
                category = match.group(1).lower()
                if category in ['internal', 'external']:
                    metadata['category'] = category
                    
        elif "присвоить отдел" in action.lower() or "assign department" in action.lower():
            match = re.search(r"['\"]([^'\"]+)['\"]", action)
            if match:
                dept_name = match.group(1)
                from backend.models.department import Department
                dept = Department.find_by_name(dept_name)
                if dept:
                    metadata['department_id'] = dept.id
                    
        elif ':' in action:
            parts = action.split(';')
            for part in parts:
                if ':' in part:
                    key, value = part.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key == 'type':
                        from backend.models.document_type import DocumentType
                        doc_type = DocumentType.find_by_name(value)
                        if doc_type:
                            metadata['document_type_id'] = doc_type.id
                            
                    elif key == 'department':
                        from backend.models.department import Department
                        dept = Department.find_by_name(value)
                        if dept:
                            metadata['department_id'] = dept.id
                            
                    elif key == 'category':
                        if value.lower() in ['internal', 'external']:
                            metadata['category'] = value.lower()
        
        return metadata
        
    except Exception as e:
        logger.error(f"Ошибка применения действия '{action}': {e}")
        return metadata


def preview_classification(file, metadata):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='classification_rules'
        """)
        
        if not cursor.fetchone():
            conn.close()
            return {
                'metadata': metadata,
                'matched_rules': []
            }
        
        cursor.execute("""
            SELECT id, name, condition_text, action_text, priority
            FROM classification_rules
            WHERE is_active = 1
            ORDER BY priority DESC, created_at DESC
        """)
        
        rules = cursor.fetchall()
        conn.close()
        
        filename = file.filename if hasattr(file, 'filename') else str(file)
        result_metadata = metadata.copy()
        matched_rules = []
        
        for rule in rules:
            condition_text = rule['condition_text']
            action_text = rule['action_text']
            
            if evaluate_conditions(condition_text, filename, result_metadata):
                matched_rules.append({
                    'id': rule['id'],
                    'name': rule['name'],
                    'condition': condition_text,
                    'action': action_text,
                    'priority': rule['priority']
                })
                result_metadata = apply_actions(action_text, result_metadata)
        
        return {
            'metadata': result_metadata,
            'matched_rules': matched_rules
        }
        
    except Exception as e:
        logger.error(f"Ошибка предпросмотра классификации: {e}")
        return {
            'metadata': metadata,
            'matched_rules': []
        }
