-- Миграция: добавление поля password в таблицу users
-- Выполнить после создания основной схемы

ALTER TABLE users ADD COLUMN password_hash TEXT;

-- Обновление существующих пользователей (временный пароль '123')
-- В реальной системе пароли должны быть захешированы
-- UPDATE users SET password_hash = 'pbkdf2:sha256:...' WHERE password_hash IS NULL;

