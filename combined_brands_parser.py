import os
import time
import json
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import requests
from requests_html import HTMLSession
import re

# ... существующий код настройки Chrome ...

class BrandParser:
    def __init__(self):
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-gpu")
        
        # Настройка путей
        self.user_home_dir = os.path.expanduser("~")
        self.chrome_binary_path = os.path.join(self.user_home_dir, "chrome-linux64", "chrome")
        self.chromedriver_path = os.path.join(self.user_home_dir, "chromedriver-linux64", "chromedriver")
        
        self.chrome_options.binary_location = self.chrome_binary_path
        self.service = Service(self.chromedriver_path)
        
        # Создаем директории для данных
        if not os.path.exists("brand_data"):
            os.makedirs("brand_data")

    def collect_unique_brand_links(self):
        """Сбор уникальных ссылок на бренды с использованием stealth"""
        print("Начинаем сбор уникальных ссылок на бренды...")
        brand_links = set()

        with webdriver.Chrome(service=self.service, options=self.chrome_options) as browser:
            stealth(browser,
                    languages=["en-US", "en"],
                    vendor="Google Inc.",
                    platform="Win32",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True,
                    )
            # Получаем ссылки категорий
            category_links = self._extract_category_links(browser)
            
            # Собираем ссылки на бренды
            for url in category_links:
                try:
                    browser.get(url)
                    WebDriverWait(browser, 10).until(
                        EC.presence_of_all_elements_located((By.XPATH, "//a[contains(text(), 'View Brand')]"))
                    )
                    
                    elements = browser.find_elements(By.XPATH, "//a[contains(text(), 'View Brand')]")
                    for element in elements:
                        link = element.get_attribute('href')
                        if link not in brand_links:
                            brand_links.add(link)
                            print(f"Найдена новая ссылка на бренд: {link}")
                            
                except Exception as e:
                    print(f"Ошибка при обработке {url}: {e}")

        # Сохраняем собранные ссылки
        self._save_links_to_csv(brand_links)
        return brand_links

    def process_brand_data(self, brand_links=None):
        """Получение JSON данных для каждого бренда"""
        if brand_links is None:
            brand_links = self._read_links_from_csv()

        print("Начинаем получение JSON данных для брендов...")
        for brand_url in brand_links:
            try:
                print(f"Обработка бренда: {brand_url}")
                
                # Получаем JSON данные
                json_data = self._get_json_data_for_brand(brand_url)
                
                if json_data:
                    # Сохраняем данные
                    brand_name = brand_url.split('/')[-1]
                    filename = os.path.join("brand_data", f"{brand_name}.json")
                    self._save_json_data(json_data, filename)
                
            except Exception as e:
                print(f"Ошибка при обработке бренда {brand_url}: {str(e)}")
                continue

    def run_full_process(self):
        """Запуск полного процесса сбора данных"""
        print("Запуск полного процесса сбора данных...")
        
        # Шаг 1: Сбор уникальных ссылок
        brand_links = self.collect_unique_brand_links()
        
        # Шаг 2: Получение JSON данных
        self.process_brand_data(brand_links)
        
        print("Процесс завершен!")

    # Вспомогательные методы
    def _extract_category_links(self, browser):
        """Извлечение ссылок категорий"""
        browser.get("https://www.knowde.com")
        WebDriverWait(browser, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//*[starts-with(@class, 'homepage-categories_tilesList')]//a"))
        )
        
        elements = browser.find_elements(By.XPATH, "//*[starts-with(@class, 'homepage-categories_tilesList')]//a")
        links = []
        for element in elements:
            link = element.get_attribute('href')
            links.append(f"{link}/brands")
            for i in range(2, 11):
                links.append(f"{link}/brands/{i}")
        return links

    def _get_json_data_for_brand(self, brand_url, max_retries=3):
        """Получение JSON данных для бренда с повторными попытками"""
        for attempt in range(max_retries):
            try:
                hash_value = self._get_hash_from_brand_page(brand_url)
                if not hash_value:
                    return None

                brand_path = brand_url.split('knowde.com')[1]
                json_url = f"https://www.knowde.com/_next/data/{hash_value}{brand_path}.json"

                session = requests.Session()
                session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })
                
                response = session.get(json_url, timeout=30)
                if response.status_code == 200:
                    return response.json()
                    
            except Exception as e:
                print(f"Попытка {attempt + 1} из {max_retries} не удалась для JSON {brand_url}: {str(e)}")
                continue
                
        print(f"Не удалось получить JSON после {max_retries} попыток для {brand_url}")
        return None

    def _get_hash_from_brand_page(self, url, max_retries=3):
        """Получение хэша со страницы бренда с повторными попытками"""
        for attempt in range(max_retries):
            try:
                session = HTMLSession()
                session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })
                response = session.get(url, timeout=30)
                script_tags = response.html.xpath('/html/head/script[@src]')
                hash_pattern = re.compile(r'/_next/static/([a-f0-9]{40})/')

                for tag in script_tags:
                    src = tag.attrs.get("src", "")
                    match = hash_pattern.search(src)
                    if match:
                        return match.group(1)
                
            except Exception as e:
                print(f"Попытка {attempt + 1} из {max_retries} не удалась для {url}: {str(e)}")
                continue
                
        print(f"Не удалось получить хэш после {max_retries} попыток для {url}")
        return None

    def _save_links_to_csv(self, links, filename="unique_brand_links.csv"):
        """Сохранение ссылок в CSV"""
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Brand URL"])
            for link in links:
                writer.writerow([link])

    def _read_links_from_csv(self, filename="unique_brand_links.csv"):
        """Чтение ссылок из CSV"""
        links = []
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)
            links = [row[0] for row in reader if row]
        return links

    def _save_json_data(self, data, filename):
        """Сохранение JSON данных"""
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    parser = BrandParser()
    parser.run_full_process()
