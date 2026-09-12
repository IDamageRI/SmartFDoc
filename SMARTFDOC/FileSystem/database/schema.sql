-- Схема базы данных для системы управления документами
-- SQLite Database Schema

-- Включаем поддержку внешних ключей
PRAGMA foreign_keys = ON;

-- Справочник отделов (создаем первым, т.к. на него ссылаются другие таблицы)
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Справочник типов документов
CREATE TABLE IF NOT EXISTS document_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE, -- 'приказ', 'заявление', 'договор', и т.д.
    description TEXT,
    category TEXT CHECK(category IS NULL OR category IN ('internal', 'external')), -- 'internal', 'external' или NULL для обоих
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    email TEXT,
    department_id INTEGER,
    role TEXT DEFAULT 'user' CHECK(role IN ('admin', 'user', 'manager')), -- 'admin', 'user', 'manager'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

-- Таблица внутренних документов
CREATE TABLE IF NOT EXISTS internal_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_type_id INTEGER,
    title TEXT NOT NULL,
    description TEXT,
    file_path TEXT NOT NULL, -- путь к файлу в файловой системе
    file_name TEXT NOT NULL,
    file_size INTEGER, -- размер файла в байтах
    file_extension TEXT CHECK(file_extension IN ('doc', 'docx', 'pdf', 'txt', 'rtf') OR file_extension IS NULL), -- 'doc', 'docx', 'pdf'
    department_id INTEGER, -- отдел, к которому относится документ
    author_id INTEGER, -- кто создал/подписал документ
    recipient_department_id INTEGER, -- отдел-получатель (если применимо)
    recipient_user_id INTEGER, -- пользователь-получатель (если применимо)
    document_date DATE, -- дата документа
    expiry_date DATE, -- срок исполнения документа
    work_status TEXT DEFAULT 'not_processed' CHECK(work_status IN ('not_processed', 'in_progress', 'completed', 'acknowledged')), -- статус работы
    completion_percent INTEGER DEFAULT 0 CHECK(completion_percent >= 0 AND completion_percent <= 100), -- доля выполнения (0-100%)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'archived', 'deleted')), -- 'active', 'archived', 'deleted'
    FOREIGN KEY (document_type_id) REFERENCES document_types(id),
    FOREIGN KEY (department_id) REFERENCES departments(id),
    FOREIGN KEY (author_id) REFERENCES users(id),
    FOREIGN KEY (recipient_department_id) REFERENCES departments(id),
    FOREIGN KEY (recipient_user_id) REFERENCES users(id)
);

-- Таблица внешних документов
CREATE TABLE IF NOT EXISTS external_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_type_id INTEGER,
    title TEXT NOT NULL,
    description TEXT,
    file_path TEXT NOT NULL, -- путь к файлу в файловой системе
    file_name TEXT NOT NULL,
    file_size INTEGER, -- размер файла в байтах
    file_extension TEXT CHECK(file_extension IN ('doc', 'docx', 'pdf', 'txt', 'rtf') OR file_extension IS NULL), -- 'doc', 'docx', 'pdf'
    sender_name TEXT, -- от кого (название организации/ФИО)
    sender_contact TEXT, -- контактные данные отправителя
    recipient_department_id INTEGER, -- отдел-получатель
    recipient_user_id INTEGER, -- пользователь-получатель
    document_date DATE, -- дата документа
    received_date DATE, -- дата получения
    expiry_date DATE, -- срок исполнения документа
    work_status TEXT DEFAULT 'not_processed' CHECK(work_status IN ('not_processed', 'in_progress', 'completed', 'acknowledged')), -- статус работы
    completion_percent INTEGER DEFAULT 0 CHECK(completion_percent >= 0 AND completion_percent <= 100), -- доля выполнения (0-100%)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'archived', 'deleted')), -- 'active', 'archived', 'deleted'
    FOREIGN KEY (document_type_id) REFERENCES document_types(id),
    FOREIGN KEY (recipient_department_id) REFERENCES departments(id),
    FOREIGN KEY (recipient_user_id) REFERENCES users(id)
);

-- Индексы для оптимизации поиска
CREATE INDEX IF NOT EXISTS idx_internal_docs_type ON internal_documents(document_type_id);
CREATE INDEX IF NOT EXISTS idx_internal_docs_department ON internal_documents(department_id);
CREATE INDEX IF NOT EXISTS idx_internal_docs_author ON internal_documents(author_id);
CREATE INDEX IF NOT EXISTS idx_internal_docs_date ON internal_documents(document_date);
CREATE INDEX IF NOT EXISTS idx_internal_docs_status ON internal_documents(status);

CREATE INDEX IF NOT EXISTS idx_external_docs_type ON external_documents(document_type_id);
CREATE INDEX IF NOT EXISTS idx_external_docs_department ON external_documents(recipient_department_id);
CREATE INDEX IF NOT EXISTS idx_external_docs_date ON external_documents(document_date);
CREATE INDEX IF NOT EXISTS idx_external_docs_status ON external_documents(status);

CREATE INDEX IF NOT EXISTS idx_users_department ON users(department_id);

-- Триггеры для автоматического обновления updated_at
CREATE TRIGGER IF NOT EXISTS update_users_timestamp 
    AFTER UPDATE ON users
    BEGIN
        UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_internal_docs_timestamp 
    AFTER UPDATE ON internal_documents
    BEGIN
        UPDATE internal_documents SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_external_docs_timestamp 
    AFTER UPDATE ON external_documents
    BEGIN
        UPDATE external_documents SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- Таблица логов загрузок
CREATE TABLE IF NOT EXISTS upload_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    category TEXT NOT NULL CHECK(category IN ('internal', 'external')),
    user_id INTEGER NOT NULL,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_upload_logs_document ON upload_logs(document_id, category);
CREATE INDEX IF NOT EXISTS idx_upload_logs_user ON upload_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_upload_logs_date ON upload_logs(uploaded_at);


