"""
Скрипт для проверки существующих дубликатов в системе
"""
from backend.services.duplicate_detector import duplicate_detector

def check_existing_duplicates():
    """Проверяет существующие дубликаты в системе"""
    print("🔍 Проверка существующих дубликатов...")
    
    duplicates = duplicate_detector.find_duplicates(method='hash')
    
    if duplicates:
        print(f"⚠️  Найдено {len(duplicates)} групп дубликатов:")
        for i, group in enumerate(duplicates):
            print(f"Группа {i+1}: {len(group)} документов")
            for doc in group:
                print(f"  - {doc['file_name']} (ID: {doc['id']})")
    else:
        print("✅ Дубликаты не найдены")

if __name__ == "__main__":
    check_existing_duplicates()

