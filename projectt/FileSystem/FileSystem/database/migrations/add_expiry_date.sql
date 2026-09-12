-- Миграция: добавление поля expiry_date в таблицы документов
-- Выполнить после создания основной схемы

-- Добавляем поле expiry_date в internal_documents
ALTER TABLE internal_documents ADD COLUMN expiry_date DATE;

-- Добавляем поле expiry_date в external_documents
ALTER TABLE external_documents ADD COLUMN expiry_date DATE;

