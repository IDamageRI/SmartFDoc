"""
Автоматический запуск проекта с инициализацией БД
"""
# -*- coding: utf-8 -*-
import sys
import io
import subprocess
from pathlib import Path

# Настройка кодировки для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def run_script(script_path, description):
    """Запускает Python скрипт"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        if result.stdout:
            print(result.stdout)
        if result.returncode != 0:
            if result.stderr:
                print(result.stderr)
            print(f"[!] Предупреждение: скрипт завершился с кодом {result.returncode}")
        return result.returncode == 0
    except Exception as e:
        print(f"[X] Ошибка при выполнении {script_path}: {e}")
        return False

def run_migration(module_name, description):
    """Запускает миграцию напрямую через импорт"""
    print(f"\n{description}...")
    try:
        if module_name == "create_notifications_table":
            from database.create_notifications_table import create_notifications_table
            create_notifications_table()
        elif module_name == "add_expiry_date":
            from database.add_expiry_date import add_expiry_date
            add_expiry_date()
        elif module_name == "update_users_passwords":
            from database.update_users_passwords import update_users_passwords
            update_users_passwords()
        print(f"[OK] {description} выполнено")
        return True
    except Exception as e:
        print(f"[!] {description}: {e}")
        return False

def main():
    """Основная функция запуска"""
    base_dir = Path(__file__).parent
    db_path = base_dir / "database" / "documents.db"
    
    print("\n" + "="*50)
    print("ЗАПУСК СИСТЕМЫ УПРАВЛЕНИЯ ДОКУМЕНТАМИ")
    print("="*50)
    
    # Проверяем наличие БД
    if not db_path.exists():
        print("\n[!] База данных не найдена, выполняется инициализация...")
        
        # Инициализация БД через backend (автоматическая)
        try:
            from backend.utils.db import init_db
            init_db()
            print("[OK] База данных создана")
        except Exception as e:
            print(f"[X] Ошибка создания БД: {e}")
            return
        
        # Добавляем отделы и пользователей
        if (base_dir / "database" / "add_users.py").exists():
            run_script("database/add_users.py", "Добавление пользователей")
        
        # Устанавливаем пароли
        run_migration("update_users_passwords", "Установка паролей")
        
        # Создаем таблицу уведомлений
        run_migration("create_notifications_table", "Создание таблицы уведомлений")
        
        # Добавляем поле expiry_date
        run_migration("add_expiry_date", "Добавление поля expiry_date")
    else:
        print("\n[OK] База данных уже существует")
        # Выполняем миграции на всякий случай
        run_migration("update_users_passwords", "Проверка паролей")
        run_migration("create_notifications_table", "Проверка таблицы уведомлений")
        run_migration("add_expiry_date", "Проверка поля expiry_date")
    
    # Запускаем сервер
    print("\n" + "="*50)
    print("ЗАПУСК СЕРВЕРА")
    print("="*50)
    print("\nСервер будет доступен по адресам:")
    print("  - http://localhost:5000")
    print("  - http://127.0.0.1:5000")
    print("\nДля остановки нажмите Ctrl+C")
    print("="*50 + "\n")
    
    # Запускаем Flask приложение
    from run import app
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)

if __name__ == "__main__":
    main()

