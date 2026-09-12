import requests
from bs4 import BeautifulSoup
import re
import time
import sys

class BankiRuFixedParser:
    def __init__(self):
        self.base_url = "https://www.banki.ru"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
        })

    def get_company_info(self, inn, kpp):
        """Получает информацию о компании по ИНН и КПП"""
        url = f"{self.base_url}/business/contragent/{inn}-{kpp}/"
        print(f"🔍 Загружаем страницу: {url}")
        
        try:
            response = self.session.get(url, timeout=10)
            print(f"📊 Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                if "contragent" in response.url:
                    print("✅ Страница компании загружена успешно!")
                    return self.parse_company_page(response.text, response.url, inn, kpp)
                else:
                    raise Exception("Не удалось загрузить страницу компании")
            else:
                raise Exception(f"Ошибка загрузки страницы: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Ошибка получения данных: {e}")

    def parse_company_page(self, html, url, inn, kpp):
        """Парсит страницу компании"""
        soup = BeautifulSoup(html, 'html.parser')
        
        print("🔍 Извлекаем данные со страницы...")
        
        company_data = {
            'ogrn': self._extract_ogrn(soup),
            'registration_date': self._extract_registration_date(soup),
            'inn': inn,
            'kpp': kpp,
            'full_name': self._extract_full_name(soup),
            'address': self._extract_address(soup),
            'director': self._extract_director(soup),
            'main_okved': self._extract_main_okved(soup),
            'status': self._extract_status(soup),
            'url': url
        }
        
        return company_data

    def _extract_ogrn(self, soup):
        """Извлекает ОГРН"""
        # Ищем в различных местах
        selectors = [
            'div:contains("ОГРН")',
            'span:contains("ОГРН")',
            'td:contains("ОГРН")',
            '[data-test*="ogrn"]'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                match = re.search(r'ОГРН[^\d]*(\d{13})', text)
                if match:
                    return match.group(1)
        
        # Ищем в общем тексте
        text = soup.get_text()
        match = re.search(r'ОГРН[^\d]*(\d{13})', text)
        if match:
            return match.group(1)
        
        return "Не найден"

    def _extract_registration_date(self, soup):
        """Извлекает дату регистрации"""
        selectors = [
            'div:contains("Дата регистрации")',
            'span:contains("Дата регистрации")',
            'td:contains("Дата регистрации")',
            '[data-test*="registration"]'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                match = re.search(r'(\d{2}\.\d{2}\.\d{4})', text)
                if match:
                    return match.group(1)
        
        text = soup.get_text()
        match = re.search(r'Дата регистрации[^\d]*(\d{2}\.\d{2}\.\d{4})', text)
        if match:
            return match.group(1)
        
        return "Не найдена"

    def _extract_full_name(self, soup):
        """Извлекает полное название"""
        # Ищем в заголовке h1
        h1 = soup.find('h1')
        if h1:
            name = h1.get_text(strip=True)
            if name and name != "Banki.ru":
                return name
        
        # Ищем в других местах
        selectors = [
            '[data-test="contragent-header"]',
            '.business-contragent-header',
            '.company-name',
            '.organization-name'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                name = element.get_text(strip=True)
                if name and name != "Banki.ru":
                    return name
        
        return "Не найдено"

    def _extract_address(self, soup):
        """Извлекает адрес"""
        selectors = [
            'div:contains("Адрес")',
            'span:contains("Адрес")',
            'td:contains("Адрес")',
            '[data-test*="address"]',
            '.business-address'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if 'Адрес' in text:
                    # Пытаемся извлечь адрес после слова "Адрес"
                    address_match = re.search(r'Адрес[^:]*:\s*([^\n]+)', text)
                    if address_match:
                        return address_match.group(1).strip()
                    else:
                        # Если нет двоеточия, берем текст после "Адрес"
                        address = text.split('Адрес')[-1].strip()
                        if address:
                            return address
        
        return "Не найден"

    def _extract_director(self, soup):
        """Извлекает руководителя"""
        selectors = [
            'div:contains("Руководитель")',
            'span:contains("Руководитель")',
            'td:contains("Руководитель")',
            '[data-test*="director"]',
            '.business-director'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if 'Руководитель' in text:
                    director_match = re.search(r'Руководитель[^:]*:\s*([^\n]+)', text)
                    if director_match:
                        return director_match.group(1).strip()
                    else:
                        director = text.split('Руководитель')[-1].strip()
                        if director:
                            return director
        
        return "Не найден"

    def _extract_main_okved(self, soup):
        """Извлекает основной ОКВЭД"""
        selectors = [
            'div:contains("ОКВЭД")',
            'span:contains("ОКВЭД")',
            'td:contains("ОКВЭД")',
            '[data-test*="okved"]',
            '.business-okved'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if 'ОКВЭД' in text:
                    okved_match = re.search(r'ОКВЭД[^:]*:\s*([^\n]+)', text)
                    if okved_match:
                        return okved_match.group(1).strip()
                    else:
                        okved = text.split('ОКВЭД')[-1].strip()
                        if okved:
                            return okved
        
        return "Не найден"

    def _extract_status(self, soup):
        """Извлекает статус"""
        # Ищем статус по тексту
        text = soup.get_text()
        
        if 'Действует' in text:
            return 'Действует'
        elif 'Ликвидирован' in text:
            return 'Ликвидирован'
        elif 'Не действует' in text:
            return 'Не действует'
        elif 'В процессе ликвидации' in text:
            return 'В процессе ликвидации'
        
        # Ищем в элементах статуса
        status_elements = soup.select('[data-test*="status"], .status, .company-status')
        for element in status_elements:
            status = element.get_text(strip=True)
            if status in ['Действует', 'Ликвидирован', 'Не действует']:
                return status
        
        return "Не определен"

    def save_to_txt(self, company_data, filename=None):
        """Сохраняет данные в txt файл"""
        if not filename:
            filename = f"company_{company_data.get('inn', 'unknown')}_{company_data.get('kpp', 'unknown')}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("ИНФОРМАЦИЯ О КОМПАНИИ\n")
            f.write("=" * 50 + "\n\n")
            
            for key, value in company_data.items():
                if key == 'url':
                    continue
                    
                key_name = {
                    'ogrn': 'ОГРН',
                    'registration_date': 'Дата регистрации',
                    'inn': 'ИНН',
                    'kpp': 'КПП',
                    'full_name': 'Полное название',
                    'address': 'Адрес организации',
                    'director': 'Руководитель',
                    'main_okved': 'Основной код ОКВЭД',
                    'status': 'Статус'
                }.get(key, key)
                
                f.write(f"{key_name}: {value}\n")
            
            f.write(f"\nСсылка: {company_data.get('url', 'Неизвестно')}")
            f.write("\n" + "=" * 50)
            f.write(f"\nСгенерировано: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return filename

def main():
    parser = BankiRuFixedParser()
    
    print("🎯 ПАРСЕР BANKI.RU (Формат: ИНН-КПП)")
    print("=" * 60)
    print("Пример URL: https://www.banki.ru/business/contragent/3666031208-482544001/")
    print("=" * 60)
    
    while True:
        print("\nВведите реквизиты компании:")
        
        inn = input("ИНН (10 или 12 цифр): ").strip()
        if inn.lower() == 'exit':
            print("👋 Завершение работы.")
            break
            
        if not inn.isdigit() or len(inn) not in [10, 12]:
            print("❌ Ошибка: ИНН должен содержать 10 или 12 цифр")
            continue
        
        kpp = input("КПП (9 цифр): ").strip()
        if not kpp.isdigit() or len(kpp) != 9:
            print("❌ Ошибка: КПП должен содержать 9 цифр")
            continue
        
        try:
            print(f"\n🔍 Поиск компании с ИНН: {inn}, КПП: {kpp}")
            company_data = parser.get_company_info(inn, kpp)
            
            print("\n" + "="*70)
            print("✅ ИНФОРМАЦИЯ О КОМПАНИИ:")
            print("="*70)
            
            info_lines = [
                f"🏢 Название: {company_data.get('full_name', 'Не найдено')}",
                f"📊 Статус: {company_data.get('status', 'Не определен')}",
                f"🔢 ОГРН: {company_data.get('ogrn', 'Не найден')}",
                f"🔢 ИНН: {company_data.get('inn', 'Не найден')}",
                f"🔢 КПП: {company_data.get('kpp', 'Не найден')}",
                f"📅 Дата регистрации: {company_data.get('registration_date', 'Не найдена')}",
                f"👤 Руководитель: {company_data.get('director', 'Не найден')}",
                f"🏠 Адрес: {company_data.get('address', 'Не найден')}",
                f"📋 Основной ОКВЭД: {company_data.get('main_okved', 'Не найден')}",
                f"🔗 Ссылка: {company_data.get('url', 'Неизвестно')}"
            ]
            
            for line in info_lines:
                print(line)
            
            save_choice = input("\n💾 Сохранить результаты в файл? (y/n): ").strip().lower()
            if save_choice in ['y', 'д', 'yes', 'да']:
                filename = parser.save_to_txt(company_data)
                print(f"✅ Данные сохранены в файл: {filename}")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")

def test_example():
    """Тестируем на примере из задания"""
    parser = BankiRuFixedParser()
    
    print("🧪 ТЕСТОВЫЙ ПРОГОН")
    print("=" * 50)
    
    test_cases = [
        ("3666031208", "482544001"),  # Пример из задания
        ("3666031208", "366601001"),  # Другой возможный КПП
    ]
    
    for inn, kpp in test_cases:
        print(f"\n🔍 Тестируем ИНН: {inn}, КПП: {kpp}")
        try:
            company_data = parser.get_company_info(inn, kpp)
            print(f"✅ Успешно: {company_data.get('full_name')}")
            print(f"📊 Статус: {company_data.get('status')}")
            print(f"🔢 ОГРН: {company_data.get('ogrn')}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        test_example()
    else:
        main()