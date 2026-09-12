# Анализ фронтенда и план интеграции

## 📋 Структура фронтенда

### Основные компоненты:

1. **Авторизация** (`#auth-window`)
   - Выбор пользователя из списка (select)
   - Поле пароля
   - Кнопка "Авторизироваться"
   - **Текущая реализация:** статический список пользователей в JS
   - **Нужно:** подключение к backend API

2. **Главное окно** (`#main-window`)
   - Header с навигацией
   - Уведомления
   - Меню пользователя
   - Контентная область

3. **Секции контента:**
   - `#personal-section` - Личный кабинет
   - `#documents-section` - Документы
   - `#classification-section` - Классификация (только админ)
   - `#search-section` - Поиск документов
   - `#stats-section` - Статистика (только админ)

4. **Модальные окна:**
   - `#document-modal` - Детали документа
   - `#upload-modal` - Загрузка документа

---

## 🔌 Требуемые API endpoints

### Авторизация
```
POST /api/auth/login
Body: { username: string, password: string }
Response: { success: bool, user: {...}, session_id: string }

GET /api/auth/me
Response: { user: {...} }

POST /api/auth/logout
```

### Документы
```
GET /api/documents
Query params: department_id, type_id, date_from, date_to, status, category, sort
Response: { documents: [...], total: number }

GET /api/documents/{id}
Response: { document: {...} }

POST /api/documents
Body: FormData (file + metadata)
Response: { success: bool, document_id: number }

PUT /api/documents/{id}
Body: { title, description, type_id, ... }
Response: { success: bool }

DELETE /api/documents/{id}
Response: { success: bool }

GET /api/documents/{id}/download
Response: File download
```

### Справочники
```
GET /api/departments
Response: { departments: [...] }

GET /api/document-types
Response: { types: [...] }

GET /api/users
Response: { users: [...] } (с учетом прав доступа)
```

### Поиск
```
GET /api/search/catalog
Query params: query, path
Response: { items: [...], path: string }

GET /api/search/content
Query params: query, filters
Response: { documents: [...] }
```

### Файловая система
```
GET /api/filesystem/tree
Response: { tree: {...} }

GET /api/filesystem/path
Query params: path
Response: { items: [...] }
```

### Уведомления
```
GET /api/notifications
Response: { notifications: [...] }

GET /api/notifications/unread
Response: { count: number, notifications: [...] }

PUT /api/notifications/{id}/read
Response: { success: bool }

DELETE /api/notifications/{id}
Response: { success: bool }
```

### Статистика (только админ)
```
GET /api/stats/overview
Response: { total_documents, processed, duplicates, ... }

GET /api/stats/departments
Response: { departments: [{ name, count, percentage }] }

GET /api/stats/sources
Response: { sources: [...] }
```

### Классификация (только админ)
```
GET /api/classification/rules
Response: { rules: [...] }

POST /api/classification/rules
Body: { name, condition, action, priority }
Response: { success: bool, rule_id: number }

PUT /api/classification/rules/{id}
Body: { ... }
Response: { success: bool }

DELETE /api/classification/rules/{id}
Response: { success: bool }
```

---

## 📝 Заметки из файла заметок.txt

### 1. Создание пользователей администратором
- Админ создает логин по ФИО (или автоматически)
- Выдает роль и пароль
- **Требуется:** API для управления пользователями (CRUD)

### 2. Вкладка "Классификация"
- Только для администратора
- Формирование правил сортировки и атрибутов
- **Требуется:** изменить фронтенд (уже есть в HTML, но нужно проверить)

### 3. CSS в отдельные файлы
- Если облегчит работу - вынести CSS
- **Решение:** пока оставить встроенным, при необходимости вынести

### 4. Редактирование файлов в предпросмотре
- Добавить возможность редактировать файлы при открытии
- **Требуется:** API для редактирования документов + сохранение версий

### 5. Поиск по каталогам
- Изменить на подходящую структуру (сейчас заглушка)
- **Требуется:** реализовать древовидную структуру файлов

---

## 🔄 План интеграции

### Этап 1: Базовая структура backend
1. Создать структуру папок `backend/`
2. Настроить Flask приложение
3. Подключить к SQLite БД
4. Создать базовые модели

### Этап 2: Авторизация
1. Реализовать `/api/auth/login` (проверка username/password)
2. Реализовать session management
3. Middleware для проверки авторизации
4. Обновить фронтенд для использования API вместо статических данных

### Этап 3: Документы (CRUD)
1. `GET /api/documents` - список с фильтрами
2. `GET /api/documents/{id}` - детали
3. `POST /api/documents` - загрузка файла + метаданные
4. `PUT /api/documents/{id}` - обновление метаданных
5. `DELETE /api/documents/{id}` - удаление
6. `GET /api/documents/{id}/download` - скачивание

### Этап 4: Справочники
1. `GET /api/departments`
2. `GET /api/document-types`
3. `GET /api/users` (с учетом прав)

### Этап 5: Поиск и файловая система
1. `GET /api/filesystem/tree` - древовидная структура
2. `GET /api/search/catalog` - поиск по каталогам
3. `GET /api/search/content` - поиск по содержимому

### Этап 6: Уведомления
1. Таблица `notifications` в БД
2. `GET /api/notifications`
3. Создание уведомлений при событиях
4. Планировщик проверки сроков

### Этап 7: Статистика и классификация
1. `GET /api/stats/*` - статистика
2. `GET/POST/PUT/DELETE /api/classification/rules` - правила классификации

### Этап 8: Админ-панель
1. CRUD пользователей
2. Управление отделами
3. Управление типами документов

---

## 🎯 Приоритеты реализации

**Высокий приоритет:**
1. Авторизация
2. Просмотр документов (список + детали)
3. Загрузка документов
4. Скачивание документов

**Средний приоритет:**
5. Поиск по каталогам
6. Уведомления
7. Редактирование документов

**Низкий приоритет:**
8. Статистика
9. Классификация
10. Админ-панель

---

## 🔧 Изменения во фронтенде (предложения)

### 1. Авторизация
**Текущее:** статический список пользователей в JS
**Нужно:** 
- Запрос к `/api/departments` для списка отделов (если нужно)
- Запрос к `/api/auth/login` при нажатии "Авторизироваться"
- Сохранение session_id в localStorage/cookie
- Проверка авторизации при загрузке страницы

### 2. Документы
**Текущее:** статические данные в JS
**Нужно:**
- Запрос к `/api/documents` при загрузке секции
- Динамическое заполнение карточек документов
- Модальное окно с деталями из API

### 3. Загрузка документов
**Текущее:** модальное окно без функционала
**Нужно:**
- FormData для отправки файла + метаданных
- POST запрос к `/api/documents`
- Обработка ответа и обновление списка

### 4. Поиск по каталогам
**Текущее:** заглушка с жестко заданными элементами
**Нужно:**
- Запрос к `/api/filesystem/tree` для получения структуры
- Рекурсивное отображение дерева
- Обработка кликов по элементам

### 5. Уведомления
**Текущее:** статические уведомления в HTML
**Нужно:**
- Запрос к `/api/notifications/unread` для счетчика
- Запрос к `/api/notifications` для списка
- Обновление при событиях (WebSocket или polling)

---

## ✅ Следующие шаги

1. Создать базовую структуру backend (Flask)
2. Реализовать авторизацию
3. Подключить фронтенд к API авторизации
4. Реализовать CRUD документов
5. Постепенно подключать остальные функции

