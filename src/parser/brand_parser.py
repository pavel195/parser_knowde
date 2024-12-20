"""Модуль для парсинга данных о брендах."""
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from requests_html import HTMLSession
import re
from typing import Set, Optional, Dict
from src.storage.brand_storage import BrandStorage

class BrandParser:
    def __init__(self, storage: BrandStorage):
        self.storage = storage
        self.setup_chrome_options()

    def setup_chrome_options(self):
        """Настройка опций Chrome"""
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-gpu")
        
        # Настройка путей из переменных окружения
        self.chrome_binary_path = os.getenv('CHROME_BINARY_PATH', os.path.expanduser("~/chrome-linux64/chrome"))
        self.chromedriver_path = os.getenv('CHROMEDRIVER_PATH', os.path.expanduser("~/chromedriver-linux64/chromedriver"))
        
        self.chrome_options.binary_location = self.chrome_binary_path
        self.service = Service(self.chromedriver_path)

    def collect_brand_links(self) -> Set[str]:
        """Сбор ссылок на бренды"""
        print("Начинаем сбор ссылок на бренды...")
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
            
            category_links = self._extract_category_links(browser)
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

        return brand_links

    def process_brands(self, brand_links: Set[str]) -> None:
        """Обработка брендов и сохранение данных"""
        print("\nНачинаем получение данных о брендах...")
        for brand_url in brand_links:
            try:
                print(f"Обработка бренда: {brand_url}")
                json_data = self._get_json_data_for_brand(brand_url)
                
                if json_data:
                    brand_name = brand_url.split('/')[-1]
                    self.storage.save_brand_data(brand_name, json_data)
                    
            except Exception as e:
                print(f"Ошибка при обработк�� бренда {brand_url}: {str(e)}")

    def _extract_category_links(self, browser) -> list:
        """Получение ссылок на категории"""
        browser.get("https://www.knowde.com")
        WebDriverWait(browser, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//*[starts-with(@class, 'homepage-categories_tilesList')]//a"))
        )
        
        elements = browser.find_elements(By.XPATH, "//*[starts-with(@class, 'homepage-categories_tilesList')]//a")
        links = []
        for element in elements:
            link = element.get_attribute('href')
            links.append(f"{link}/brands")
            for i in range(2, 11):  # Пагинация
                links.append(f"{link}/brands/{i}")
        return links

    def _get_json_data_for_brand(self, brand_url: str, max_retries: int = 3) -> Optional[Dict]:
        """Получение JSON данных для бренда"""
        for attempt in range(max_retries):
            try:
                hash_value = self._get_hash_from_brand_page(brand_url)
                if not hash_value:
                    return None

                brand_path = brand_url.split('knowde.com')[1]
                json_url = f"https://www.knowde.com/_next/data/{hash_value}{brand_path}.json"

                session = requests.Session()
                session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                response = session.get(json_url, timeout=30)
                if response.status_code == 200:
                    return response.json()
                    
            except Exception as e:
                print(f"Попытка {attempt + 1} из {max_retries} не удалась для JSON {brand_url}: {str(e)}")
                continue
                
        return None

    def _get_hash_from_brand_page(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Получение хэша со страницы бренда"""
        for attempt in range(max_retries):
            try:
                session = HTMLSession()
                session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
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
                
        return None
