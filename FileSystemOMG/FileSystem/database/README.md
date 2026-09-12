# База данных системы управления документами

## Описание

SQLite база данных для хранения информации о документах компании (внутренних и внешних), пользователях и справочниках.

## Структура базы данных

### Основные таблицы

1. **users** - Пользователи системы
   - `id` - Уникальный идентификатор
   - `username` - Имя пользователя (уникальное)
   - `full_name` - Полное имя
   - `email` - Email
   - `department_id` - Связь с отделом
   - `role` - Роль (admin, user, manager)
   - `created_at`, `updated_at` - Временные метки

2. **internal_documents** - Внутренние документы
   - `id` - Уникальный идентификатор
   - `document_type_id` - Тип документа
   - `title` - Название документа
   - `description` - Описание
   - `file_path` - Путь к файлу в файловой системе
   - `file_name` - Имя файла
   - `file_size` - Размер файла в байтах
   - `file_extension` - Расширение файла (doc, docx, pdf)
   - `department_id` - Отдел документа
   - `author_id` - Автор/подписант
   - `recipient_department_id` - Отдел-получатель
   - `recipient_user_id` - Пользователь-получатель
   - `document_date` - Дата документа
   - `status` - Статус (active, archived, deleted)
   - `created_at`, `updated_at` - Временные метки

3. **external_documents** - Внешние документы
   - `id` - Уникальный идентификатор
   - `document_type_id` - Тип документа
   - `title` - Название документа
   - `description` - Описание
   - `file_path` - Путь к файлу в файловой системе
   - `file_name` - Имя файла
   - `file_size` - Размер файла в байтах
   - `file_extension` - Расширение файла
   - `sender_name` - От кого (название организации/ФИО)
   - `sender_contact` - Контактные данные отправителя
   - `recipient_department_id` - Отдел-получатель
   - `recipient_user_id` - Пользователь-получатель
   - `document_date` - Дата документа
   - `received_date` - Дата получения
   - `status` - Статус (active, archived, deleted)
   - `created_at`, `updated_at` - Временные метки

### Справочники

1. **departments** - Отделы компании
   - `id` - Уникальный идентификатор
   - `name` - Название отдела (уникальное)
   - `description` - Описание

2. **document_types** - Типы документов
   - `id` - Уникальный идентификатор
   - `name` - Название типа (приказ, заявление, договор и т.д.)
   - `description` - Описание
   - `category` - Категория (internal, external, или NULL для обоих)

## Развертывание

### Инициализация базы данных

```bash
python database/init_db.py
```

Или с указанием пути к БД:

```bash
python database/init_db.py my_database.db
```

### Заполнение тестовыми данными (опционально)

```bash
python database/seed_data.py
```

## Расширение структуры

База данных спроектирована с учетом будущих изменений:

1. **Добавление новых полей** - можно использовать `ALTER TABLE` для добавления колонок
2. **Новые справочники** - создаются по аналогии с существующими
3. **Дополнительные таблицы** - можно добавлять без изменения существующих

### Пример добавления нового поля

```sql
ALTER TABLE internal_documents ADD COLUMN priority TEXT DEFAULT 'normal';
```

### Пример создания нового справочника

```sql
CREATE TABLE IF NOT EXISTS document_statuses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Индексы

Для оптимизации поиска созданы индексы на часто используемых полях:
- Типы документов
- Отделы
- Авторы/получатели
- Даты
- Статусы

## Триггеры

Автоматическое обновление поля `updated_at` при изменении записей в таблицах:
- `users`
- `internal_documents`
- `external_documents`

## Примечания

- Файлы документов хранятся в файловой системе, в БД сохраняются только пути к ним
- Поддерживаются форматы: doc, docx, pdf, txt, rtf
- Структура легко расширяется через миграции
- Включена поддержка внешних ключей (PRAGMA foreign_keys = ON)
- Добавлены CHECK-ограничения для валидации данных (роли, статусы, расширения файлов)


