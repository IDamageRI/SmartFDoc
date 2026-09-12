import imapclient
import email
from email.header import decode_header
import os
import hashlib
import json

class MailDownloader:
    def __init__(self, server, email, password):
        self.server = server
        self.email = email
        self.password = password
        self.client = None
        self.history_file = './download_history.json'
        self.downloaded = self.load_history()
    
    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return set(json.load(f))
            except:
                return set()
        return set()
    
    def save_history(self):
        try:
            with open(self.history_file, 'w') as f:
                json.dump(list(self.downloaded), f)
        except:
            pass
    
    def connect(self):
        try:
            self.client = imapclient.IMAPClient(self.server, ssl=True)
            self.client.login(self.email, self.password)
            print("Успешное подключение")
            return True
        except:
            print("Ошибка подключения")
            return False
    
    def disconnect(self):
        if self.client:
            self.client.logout()
    
    def download_files(self):
        if not os.path.exists('./files'):
            os.makedirs('./files')
        
        new_files = []
        
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
                        
                        for part in email_message.walk():
                            if part.get_content_disposition() == 'attachment':
                                filename = part.get_filename()
                                if filename:
                                    clean_name = self.clean_filename(filename)
                                    file_types = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'rtf', 'jpg', 'jpeg']
                                    file_ext = clean_name.split('.')[-1].lower()
                                    
                                    if file_ext in file_types:
                                        file_data = part.get_payload(decode=True)
                                        if file_data:
                                            file_hash = hashlib.md5(file_data).hexdigest()
                                            
                                            if file_hash in self.downloaded:
                                                continue
                                            
                                            file_path = f'./files/{clean_name}'
                                            counter = 1
                                            while os.path.exists(file_path):
                                                name, ext = os.path.splitext(clean_name)
                                                file_path = f'./files/{name}_{counter}{ext}'
                                                counter += 1
                                            
                                            with open(file_path, 'wb') as f:
                                                f.write(file_data)
                                            
                                            self.downloaded.add(file_hash)
                                            new_files.append(file_path)
                                            print(f"Скачан: {os.path.basename(file_path)}")
                
                except:
                    continue
            
            self.save_history()
        
        except Exception as e:
            print(f"Ошибка: {e}")
        
        return new_files
    
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

def main():
    print("Загрузчик документов")
    
    email = input("Почта: ")
    password = input("Пароль: ")
    
    downloader = MailDownloader('imap.yandex.ru', email, password)
    
    if downloader.connect():
        files = downloader.download_files()
        
        if files:
            print(f"Новых файлов: {len(files)}")
        else:
            print("Новых файлов нет")
        
        downloader.disconnect()

if __name__ == "__main__":
    main()