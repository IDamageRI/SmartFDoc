# Backend системы управления документами

## Структура проекта

```
backend/
├── app.py                 # Главный файл приложения
├── config.py             # Конфигурация
├── models/               # Модели данных
│   ├── user.py
│   ├── document.py
│   ├── department.py
│   ├── document_type.py
│   └── notification.py
├── routes/               # API endpoints
│   ├── auth.py          # Авторизация
│   ├── references.py    # Справочники
│   ├── documents.py     # Документы (CRUD)
│   ├── notifications.py # Уведомления
│   ├── filesystem.py    # Файловая система
│   └── search.py        # Поиск
├── services/            # Бизнес-логика
│   ├── permissions.py   # Проверка прав
│   ├── file_manager.py # Управление файлами
│   └── notifications.py # Создание уведомлений
└── utils/               # Утилиты
    ├── db.py           # Работа с БД
    ├── validators.py   # Валидация
    └── middleware.py  # Middleware
```

## Запуск

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск сервера
python run.py
```

Сервер будет доступен по адресу: `http://localhost:5000`

## API Endpoints

### Авторизация
- `POST /api/auth/login` - Вход в систему
  ```json
  {
    "username": "admin",
    "password": "123"
  }
  ```
- `POST /api/auth/logout` - Выход
- `GET /api/auth/me` - Текущий пользователь

### Справочники
- `GET /api/departments` - Список отделов
- `GET /api/document-types` - Типы документов

### Документы
- `GET /api/documents` - Список документов (с фильтрами)
  - Query params: `category`, `department_id`, `type_id`, `author_id`, `date_from`, `date_to`, `status`, `sort`
- `GET /api/documents/{id}` - Детали документа
  - Query params: `category` (internal/external)
- `POST /api/documents` - Создание документа + загрузка файла
  - FormData: `file`, `category`, `document_type_id`, `title`, `description`, `department_id`, `document_date`, `expiry_date`, и др.
- `PUT /api/documents/{id}` - Обновление метаданных
  - Body: JSON с полями для обновления
- `DELETE /api/documents/{id}` - Удаление (soft delete)
  - Query params: `category`
- `GET /api/documents/{id}/download` - Скачивание файла
  - Query params: `category`

### Уведомления
- `GET /api/notifications` - Список уведомлений
  - Query params: `unread_only` (true/false)
- `GET /api/notifications/unread` - Непрочитанные уведомления
- `PUT /api/notifications/{id}/read` - Отметить как прочитанное
- `DELETE /api/notifications/{id}` - Удалить уведомление

### Файловая система
- `GET /api/filesystem/tree` - Древовидная структура
  - Query params: `category` (internal/external)
- `GET /api/filesystem/path` - Содержимое пути
  - Query params: `category`, `path`
- `GET /api/filesystem/browse` - Просмотр как файловый менеджер
  - Query params: `category`, `path`

### Поиск
- `GET /api/search/catalog` - Поиск по каталогам (файловой системе)
  - Query params: `query`, `category`, `path`
- `GET /api/search/content` - Поиск по содержимому (метаданным)
  - Query params: `query`, `category`, `department_id`, `type_id`

## Структура файлов

Файлы сохраняются по структуре:
```
storage/
├── internal/
│   └── {department}/
│       └── {year}/
│           └── {document_type}/
│               └── {document_date}/
│                   └── {expiry_date}/
│                       └── {filename}
└── external/
    └── (аналогичная структура)
```

## Права доступа

- **Администратор** - полный доступ ко всем документам
- **Руководитель отдела** - доступ к документам своего отдела
- **Обычный сотрудник** - доступ к документам отдела + личным + адресованным ему

## Уведомления

Уведомления создаются автоматически при:
- Загрузке документа (автору)
- Получении документа (получателю)
- Новом документе в отделе (всем сотрудникам отдела)
- Приближении срока истечения (за 3 и 1 день)

## Текущий статус

✅ Базовая структура
✅ Модели данных
✅ Авторизация (login/logout/session)
✅ Справочники
✅ CRUD документов
✅ Загрузка файлов
✅ Скачивание файлов
✅ Проверка прав доступа
✅ Уведомления
✅ Файловая система (дерево, просмотр)
✅ Поиск (по каталогам и содержимому)
⏳ Статистика (в разработке)
⏳ Классификация документов (в разработке)

## Тестовые пользователи

Все пользователи имеют временный пароль: `123`

- `admin` - Администратор
- `director_it` - Руководитель IT-отдела
- `employee_procurement_1` - Сотрудник отдела закупок
