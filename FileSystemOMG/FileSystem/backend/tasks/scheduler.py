"""
Планировщик задач
"""
import schedule
import time
from backend.services.expiry_checker import run_expiry_check


def start_scheduler():
    """Запускает планировщик задач"""
    # Проверка сроков документов каждый день в 9:00
    schedule.every().day.at("09:00").do(run_expiry_check)
    
    # Также можно запускать каждые 6 часов для более оперативных уведомлений
    schedule.every(6).hours.do(run_expiry_check)
    
    print("✓ Планировщик запущен")
    print("  - Проверка сроков документов: каждый день в 09:00 и каждые 6 часов")
    
    # Запускаем проверку сразу при старте
    run_expiry_check()
    
    # Основной цикл
    while True:
        schedule.run_pending()
        time.sleep(60)  # Проверяем каждую минуту


if __name__ == "__main__":
    start_scheduler()

