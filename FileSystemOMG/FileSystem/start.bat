@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo ЗАПУСК СИСТЕМЫ УПРАВЛЕНИЯ ДОКУМЕНТАМИ
echo ========================================
echo.

REM Проверяем наличие БД
if not exist "database\documents.db" (
    echo База данных не найдена, выполняется инициализация...
    python -c "from backend.utils.db import init_db; init_db(); print('БД создана')"
    if exist "database\add_users.py" (
        python database\add_users.py
    )
    python database\update_users_passwords.py
    python database\create_notifications_table.py
    python database\add_expiry_date.py
) else (
    echo База данных уже существует
)

echo.
echo ========================================
echo ЗАПУСК СЕРВЕРА
echo ========================================
echo.
echo Сервер будет доступен по адресам:
echo   - http://localhost:5000
echo   - http://127.0.0.1:5000
echo.
echo Для остановки нажмите Ctrl+C
echo ========================================
echo.

python run.py

