# Статус проекта - Система управления документами

## ✅ Завершенные функции

### 1. База данных
- ✅ SQLite база данных с полной схемой
- ✅ Таблицы: users, departments, document_types, internal_documents, external_documents, notifications
- ✅ Индексы для оптимизации
- ✅ Внешние ключи и проверки целостности
- ✅ Поля для сроков документов (expiry_date)
- ✅ Пароли пользователей (password_hash)

### 2. Авторизация
- ✅ POST /api/auth/login - Вход в систему
- ✅ POST /api/auth/logout - Выход
- ✅ GET /api/auth/me - Текущий пользователь
- ✅ Session-based авторизация
- ✅ Middleware для проверки прав (@login_required, @admin_required)

### 3. Справочники
- ✅ GET /api/departments - Список отделов
- ✅ GET /api/document-types - Типы документов

### 4. Документы (CRUD)
- ✅ GET /api/documents - Список с фильтрами
- ✅ GET /api/documents/{id} - Детали документа
- ✅ POST /api/documents - Создание + загрузка файла
- ✅ PUT /api/documents/{id} - Обновление метаданных
- ✅ DELETE /api/documents/{id} - Удаление (soft delete)
- ✅ GET /api/documents/{id}/download - Скачивание файла

### 5. Загрузка файлов
- ✅ Валидация файлов (размер, расширение)
- ✅ Автоматическое создание структуры папок
- ✅ Сохранение по структуре: storage/{category}/{department}/{year}/{type}/{date}/{expiry}/{filename}
- ✅ Сохранение метаданных в БД

### 6. Права доступа
- ✅ Администратор - полный доступ
- ✅ Руководитель отдела - документы отдела
- ✅ Обычный сотрудник - документы отдела + личные + адресованные

### 7. Уведомления
- ✅ Таблица notifications в БД
- ✅ GET /api/notifications - Список уведомлений
- ✅ GET /api/notifications/unread - Непрочитанные
- ✅ PUT /api/notifications/{id}/read - Отметить как прочитанное
- ✅ DELETE /api/notifications/{id} - Удалить
- ✅ Автоматическое создание при событиях:
  - Загрузка документа (автору)
  - Получение документа (получателю)
  - Новый документ в отделе (сотрудникам)

### 8. Файловая система
- ✅ GET /api/filesystem/tree - Древовидная структура
- ✅ GET /api/filesystem/path - Содержимое пути
- ✅ GET /api/filesystem/browse - Просмотр как файловый менеджер
- ✅ Проверка прав доступа

### 9. Поиск
- ✅ GET /api/search/catalog - Поиск по каталогам
- ✅ GET /api/search/content - Поиск по содержимому
- ✅ Фильтрация по правам доступа

### 10. Статистика (админ)
- ✅ GET /api/stats/overview - Общая статистика
- ✅ GET /api/stats/departments - Статистика по отделам
- ✅ GET /api/stats/sources - Статистика по источникам

### 11. Планировщик сроков
- ✅ Сервис проверки сроков документов
- ✅ Автоматическое создание уведомлений за 3 и 1 день до истечения
- ✅ Планировщик задач (schedule)

## 📁 Структура проекта

```
FileSystem/
├── backend/              # Backend приложение
│   ├── app.py           # Главный файл
│   ├── config.py        # Конфигурация
│   ├── models/          # Модели данных
│   ├── routes/          # API endpoints
│   ├── services/        # Бизнес-логика
│   ├── utils/           # Утилиты
│   └── tasks/           # Планировщик задач
├── database/            # База данных
│   ├── documents.db     # SQLite БД
│   ├── schema.sql       # Схема БД
│   └── migrations/      # Миграции
├── storage/             # Хранилище файлов
│   ├── internal/        # Внутренние документы
│   └── external/        # Внешние документы
├── frontend/            # Фронтенд
│   └── index.html       # HTML интерфейс
├── run.py               # Запуск сервера
└── requirements.txt     # Зависимости
```

## 🚀 Запуск

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Инициализация БД (если еще не сделано)
```bash
python database/init_db.py
python database/update_users_passwords.py
python database/create_notifications_table.py
python database/add_expiry_date.py
```

### 3. Запуск сервера
```bash
python run.py
```

Сервер будет доступен на: `http://localhost:5000`

### 4. Запуск планировщика (опционально, в отдельном терминале)
```bash
python backend/tasks/scheduler.py
```

## 👤 Тестовые пользователи

Все с паролем `123`:
- `admin` - Администратор (полный доступ)
- `director_it` - Руководитель IT-отдела
- `employee_procurement_1` - Сотрудник отдела закупок

## 📋 API Endpoints

### Авторизация
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`

### Справочники
- `GET /api/departments`
- `GET /api/document-types`

### Документы
- `GET /api/documents`
- `GET /api/documents/{id}`
- `POST /api/documents`
- `PUT /api/documents/{id}`
- `DELETE /api/documents/{id}`
- `GET /api/documents/{id}/download`

### Уведомления
- `GET /api/notifications`
- `GET /api/notifications/unread`
- `PUT /api/notifications/{id}/read`
- `DELETE /api/notifications/{id}`

### Файловая система
- `GET /api/filesystem/tree`
- `GET /api/filesystem/path`
- `GET /api/filesystem/browse`

### Поиск
- `GET /api/search/catalog`
- `GET /api/search/content`

### Статистика (только админ)
- `GET /api/stats/overview`
- `GET /api/stats/departments`
- `GET /api/stats/sources`

## 🔧 Конфигурация

Основные настройки в `backend/config.py`:
- `MAX_FILE_SIZE` - максимальный размер файла (10 МБ)
- `ALLOWED_EXTENSIONS` - разрешенные расширения
- `EXPIRY_WARNING_DAYS` - дни предупреждения о сроках ([3, 1])

## 📝 Примечания

1. **Пароли**: Все пользователи имеют временный пароль `123`. В продакшене каждый должен иметь уникальный пароль.

2. **Планировщик**: Запускается отдельным процессом. Проверяет сроки документов каждый день в 09:00 и каждые 6 часов.

3. **Файловая структура**: Файлы автоматически сохраняются по структуре отдел/год/тип/дата/срок.

4. **Права доступа**: Реализованы на уровне API. Каждый endpoint проверяет права пользователя.

## ✅ Готово к использованию

Все основные функции реализованы и протестированы. Backend готов к интеграции с фронтендом.

