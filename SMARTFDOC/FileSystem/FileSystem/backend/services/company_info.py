import re

try:
    import requests
    from bs4 import BeautifulSoup
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

class CompanyInfoService:
    def __init__(self):
        if not REQUESTS_AVAILABLE:
            raise ImportError('Библиотеки requests и beautifulsoup4 не установлены. Установите: pip install requests beautifulsoup4')
        
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
        
        try:
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                if "contragent" in response.url:
                    return self.parse_company_page(response.text, inn, kpp)
                else:
                    raise Exception("Не удалось загрузить страницу компании")
            else:
                raise Exception(f"Ошибка загрузки страницы: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Ошибка получения данных: {e}")

    def parse_company_page(self, html, inn, kpp):
        """Парсит страницу компании"""
        soup = BeautifulSoup(html, 'html.parser')
        
        company_data = {
            'inn': inn,
            'kpp': kpp,
            'full_name': self._extract_full_name(soup),
            'ogrn': self._extract_ogrn(soup),
            'registration_date': self._extract_registration_date(soup),
            'address': self._extract_address(soup),
            'director': self._extract_director(soup),
            'main_okved': self._extract_main_okved(soup),
            'status': self._extract_status(soup),
        }
        
        return company_data

    def _extract_ogrn(self, soup):
        """Извлекает ОГРН"""
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
        
        text = soup.get_text()
        match = re.search(r'ОГРН[^\d]*(\d{13})', text)
        if match:
            return match.group(1)
        
        return None

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
        
        return None

    def _extract_full_name(self, soup):
        """Извлекает полное название"""
        h1 = soup.find('h1')
        if h1:
            name = h1.get_text(strip=True)
            if name and name != "Banki.ru":
                return name
        
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
        
        return None

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
                    address_match = re.search(r'Адрес[^:]*:\s*([^\n]+)', text)
                    if address_match:
                        return address_match.group(1).strip()
                    else:
                        address = text.split('Адрес')[-1].strip()
                        if address:
                            return address
        
        return None

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
        
        return None

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
        
        return None

    def _extract_status(self, soup):
        """Извлекает статус"""
        text = soup.get_text()
        
        if 'Действует' in text:
            return 'Действует'
        elif 'Ликвидирован' in text:
            return 'Ликвидирован'
        elif 'Не действует' in text:
            return 'Не действует'
        elif 'В процессе ликвидации' in text:
            return 'В процессе ликвидации'
        
        status_elements = soup.select('[data-test*="status"], .status, .company-status')
        for element in status_elements:
            status = element.get_text(strip=True)
            if status in ['Действует', 'Ликвидирован', 'Не действует']:
                return status
        
        return None

