# Быстрый старт

## Шаг 1: Установка зависимостей

```bash
pip install -r requirements.txt
```

## Шаг 2: Инициализация базы данных

Выполните все миграции (если еще не выполнены):

```bash
# Основная схема БД
python database/init_db.py

# Добавление паролей пользователям
python database/update_users_passwords.py

# Создание таблицы уведомлений
python database/create_notifications_table.py

# Добавление поля expiry_date
python database/add_expiry_date.py

# (Опционально) Добавление тестовых пользователей
python database/add_users.py
```

## Шаг 3: Запуск сервера

```bash
python run.py
```

Сервер запустится на `http://localhost:5000`

## Шаг 4: (Опционально) Запуск планировщика

В отдельном терминале:

```bash
python backend/tasks/scheduler.py
```

Планировщик будет проверять сроки документов каждый день в 09:00 и каждые 6 часов.

## Тестирование

### 1. Проверка авторизации

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "123"}'
```

### 2. Получение списка отделов

```bash
curl http://localhost:5000/api/departments \
  -H "Cookie: document_session=YOUR_SESSION_ID"
```

### 3. Просмотр документов

```bash
curl http://localhost:5000/api/documents \
  -H "Cookie: document_session=YOUR_SESSION_ID"
```

## Веб-интерфейс

Откройте в браузере: `http://localhost:5000`

## Тестовые пользователи

- **admin** / **123** - Администратор
- **director_it** / **123** - Руководитель IT-отдела  
- **employee_procurement_1** / **123** - Сотрудник отдела закупок

## Структура файлов

После загрузки документов они будут сохраняться в:
```
storage/
├── internal/
│   └── {отдел}/
│       └── {год}/
│           └── {тип документа}/
│               └── {дата}/
│                   └── {срок исполнения}/
│                       └── {файл}
└── external/
    └── (аналогичная структура)
```

## Проблемы?

1. **Ошибка импорта модулей**: Убедитесь, что все зависимости установлены
2. **Ошибка БД**: Проверьте, что выполнены все миграции
3. **Порт занят**: Измените порт в `run.py` (по умолчанию 5000)

