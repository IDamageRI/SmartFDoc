import imapclient
import email
import email.utils
from email.header import decode_header
from pathlib import Path
from datetime import datetime
import hashlib
import json
import os
import re
from backend.config import STORAGE_EXTERNAL, BASE_DIR
from backend.services.file_manager import get_file_extension, get_file_size
from backend.utils.db import get_db_connection


class MailLoader:
    def __init__(self, server, email_address, password):
        self.server = server
        self.email = email_address
        self.password = password
        self.client = None
        self.history_file = BASE_DIR / 'mail_download_history.json'
        self.downloaded = self.load_history()
    
    def load_history(self):
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return set(json.load(f))
            except:
                return set()
        return set()
    
    def save_history(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.downloaded), f, ensure_ascii=False)
        except:
            pass
    
    def connect(self):
        try:
            self.client = imapclient.IMAPClient(self.server, ssl=True)
            self.client.login(self.email, self.password)
            return True
        except Exception as e:
            print(f"Ошибка подключения к почте: {e}")
            return False
    
    def disconnect(self):
        if self.client:
            try:
                self.client.logout()
            except:
                pass
    
    def clean_filename(self, filename):
        try:
            parts = decode_header(filename)
            clean_name = ''
            for part, encoding in parts:
                if isinstance(part, bytes):
                    if encoding:
                        clean_name += part.decode(encoding)
                    else:
                        clean_name += part.decode('utf-8', errors='ignore')
                else:
                    clean_name += part
            return clean_name
        except:
            return filename
    
    def extract_sender_email(self, email_message):
        """Извлекает email адрес отправителя из письма"""
        from_header = email_message.get('From', '')
        if not from_header:
            return None
        
        try:
            # Парсим заголовок From: "Name <email@example.com>" или "email@example.com"
            from_tuple = email.utils.parseaddr(from_header)
            sender_email = from_tuple[1]  # email адрес
            
            if sender_email and '@' in sender_email:
                return sender_email.lower().strip()
        except Exception as e:
            print(f"Ошибка парсинга email отправителя: {e}")
        
        # Если не удалось распарсить, пытаемся извлечь напрямую
        if '@' in from_header:
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', from_header)
            if email_match:
                return email_match.group(0).lower().strip()
        
        return None
    
    def extract_department_from_email(self, email_message):
        """Извлекает отдел из получателей письма"""
        to_addresses = email_message.get_all('To', [])
        cc_addresses = email_message.get_all('Cc', [])
        all_addresses = to_addresses + cc_addresses
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for addr in all_addresses:
            if isinstance(addr, tuple):
                addr = addr[1]
            email_addr = addr.lower()
            
            cursor.execute("SELECT department_id FROM users WHERE email = ?", (email_addr,))
            row = cursor.fetchone()
            if row and row['department_id']:
                cursor.execute("SELECT name FROM departments WHERE id = ?", (row['department_id'],))
                dept_row = cursor.fetchone()
                conn.close()
                if dept_row:
                    return dept_row['name']
        
        conn.close()
        return None
    
    def extract_date_from_email(self, email_message):
        """Извлекает дату из письма"""
        date_str = email_message.get('Date')
        if date_str:
            try:
                date_tuple = email.utils.parsedate_tz(date_str)
                if date_tuple:
                    date_obj = datetime(*date_tuple[:6])
                    return date_obj.date()
            except:
                pass
        return datetime.now().date()
    
    def extract_document_type_from_filename(self, filename):
        """Определяет тип документа по имени файла"""
        filename_lower = filename.lower()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM document_types")
        types = cursor.fetchall()
        conn.close()
        
        for doc_type in types:
            type_name_lower = doc_type['name'].lower()
            if type_name_lower in filename_lower:
                return doc_type['id'], doc_type['name']
        
        return None, 'unknown'
    
    def download_and_process_files(self):
        """Загружает файлы с почты и обрабатывает их"""
        if not self.client:
            return []
        
        new_documents = []
        
        try:
            self.client.select_folder('INBOX')
            messages = self.client.search(['ALL'])
            
            for msg_id in messages:
                try:
                    raw_message = self.client.fetch([msg_id], ['BODY[]'])
                    message_data = raw_message[msg_id]
                    
                    if b'BODY[]' in message_data:
                        email_body = message_data[b'BODY[]']
                        email_message = email.message_from_bytes(email_body)
                        
                        department_name = self.extract_department_from_email(email_message)
                        document_date = self.extract_date_from_email(email_message)
                        sender_name = email_message.get('From', 'Неизвестный отправитель')
                        sender_email = self.extract_sender_email(email_message)
                        
                        for part in email_message.walk():
                            if part.get_content_disposition() == 'attachment':
                                filename = part.get_filename()
                                if filename:
                                    clean_name = self.clean_filename(filename)
                                    file_ext = clean_name.split('.')[-1].lower() if '.' in clean_name else ''
                                    
                                    if file_ext in ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'rtf', 'jpg', 'jpeg', 'txt']:
                                        file_data = part.get_payload(decode=True)
                                        if file_data:
                                            file_hash = hashlib.md5(file_data).hexdigest()
                                            
                                            if file_hash in self.downloaded:
                                                continue
                                            
                                            document_type_id, document_type_name = self.extract_document_type_from_filename(clean_name)
                                            
                                            year = document_date.year
                                            
                                            file_path = self.generate_file_path(
                                                department_name or 'unknown',
                                                year,
                                                sender_email or 'unknown_sender',
                                                document_date,
                                                clean_name
                                            )
                                            
                                            file_path.parent.mkdir(parents=True, exist_ok=True)
                                            
                                            with open(file_path, 'wb') as f:
                                                f.write(file_data)
                                            
                                            self.downloaded.add(file_hash)
                                            
                                            relative_path = file_path.relative_to(BASE_DIR)
                                            
                                            new_documents.append({
                                                'file_path': str(relative_path),
                                                'file_name': clean_name,
                                                'file_size': len(file_data),
                                                'file_extension': file_ext,
                                                'department_name': department_name,
                                                'document_type_id': document_type_id,
                                                'document_type_name': document_type_name,
                                                'document_date': document_date.isoformat(),
                                                'sender_name': sender_name,
                                                'sender_email': sender_email,
                                                'title': clean_name.rsplit('.', 1)[0] if '.' in clean_name else clean_name
                                            })
                                            
                                            print(f"Обработан файл: {clean_name}")
                
                except Exception as e:
                    print(f"Ошибка обработки письма {msg_id}: {e}")
                    continue
            
            self.save_history()
        
        except Exception as e:
            print(f"Ошибка загрузки файлов: {e}")
        
        return new_documents
    
    def generate_file_path(self, department_name, year, sender_email, document_date, filename):
        """Генерирует путь для файла с почты по схеме: Корпоративная почта/год/email_отправителя/дата/файл"""
        def sanitize(name):
            if not name:
                return "unknown"
            invalid_chars = '<>:"/\\|?*'
            for char in invalid_chars:
                name = name.replace(char, '_')
            return name.strip() or "unknown"
        
        if isinstance(document_date, str):
            date_str = document_date[:10]
        elif isinstance(document_date, datetime):
            date_str = document_date.strftime('%Y-%m-%d')
        else:
            date_str = str(document_date)[:10]
        
        # Для файлов с почты: Корпоративная почта/год/email_отправителя/дата/файл
        # Папка "Корпоративная почта" наравне с отделами
        path_parts = [
            'Корпоративная почта',
            str(year),
            sanitize(sender_email) if sender_email else 'unknown_sender',
            date_str
        ]
        
        file_path = STORAGE_EXTERNAL
        for part in path_parts:
            if part:
                file_path = file_path / part
        
        file_path = file_path / filename
        
        counter = 1
        original_path = file_path
        while file_path.exists():
            name = Path(filename).stem
            ext = Path(filename).suffix
            file_path = original_path.parent / f"{name}_{counter}{ext}"
            counter += 1
        
        return file_path

