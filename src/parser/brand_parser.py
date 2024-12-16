"""Модуль для парсинга данных о брендах."""
import os
import random
import time
from fake_useragent import UserAgent
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
from dotenv import load_dotenv

class BrandParser:
    def __init__(self, storage: BrandStorage):
        self.storage = storage
        self.user_agent = UserAgent()
        load_dotenv()  # Загружаем переменные окружения
        self.chrome_binary_path = os.getenv('CHROME_BINARY_PATH')
        self.chromedriver_path = os.getenv('CHROMEDRIVER_PATH')
        self.setup_chrome_options()

    def setup_chrome_options(self):
        """Настройка опций Chrome для антидетекта"""
        try:
            print("\nНастройка Chrome опций...")
            self.chrome_options = Options()
            
            # Устанавливаем путь к бинарному файлу Chrome
            if self.chrome_binary_path:
                print(f"Используем Chrome: {self.chrome_binary_path}")
                self.chrome_options.binary_location = self.chrome_binary_path
            
            # Основные настройки Chrome
            self.chrome_options.add_argument('--no-sandbox')
            self.chrome_options.add_argument('--disable-dev-shm-usage')
            self.chrome_options.add_argument('--disable-gpu')
            self.chrome_options.add_argument('--remote-debugging-port=9222')
            
            # Антидетект настройки
            self.chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            self.chrome_options.add_argument(f'--user-agent={self.user_agent.random}')
            self.chrome_options.add_argument('--disable-infobars')
            self.chrome_options.add_argument('--disable-browser-side-navigation')
            
            # Настройка языка и разрешения
            self.chrome_options.add_argument('--lang=en-US,en;q=0.9')
            self.chrome_options.add_argument('--window-size=1920,1080')
            
            # Проверяем существование файлов
            if os.path.exists(self.chrome_binary_path):
                print("Chrome executable найден")
            else:
                print(f"ОШИБКА: Chrome не найден по пути: {self.chrome_binary_path}")
                
            if os.path.exists(self.chromedriver_path):
                print("ChromeDriver найден")
            else:
                print(f"ОШИБКА: ChromeDriver не найден по пути: {self.chromedriver_path}")
                
            # Проверяем права на выполнение
            if os.access(self.chromedriver_path, os.X_OK):
                print("ChromeDriver имеет права на выполнение")
            else:
                print("ВНИМАНИЕ: ChromeDriver не имеет прав на выполнение")
                print("Пробуем установить права...")
                try:
                    os.chmod(self.chromedriver_path, 0o755)
                    print("Права установлены")
                except Exception as e:
                    print(f"Ошибка при установке прав: {e}")
            
            print("\nНастройка Chrome опций завершена")
            
        except Exception as e:
            print(f"\nОШИБКА при настройке Chrome: {str(e)}")
            raise

    def init_webdriver(self):
        """Инициализация веб-драйвера"""
        try:
            print("\nИнициализация веб-драйвера...")
            if not self.chromedriver_path:
                raise ValueError("Путь к ChromeDriver не указан в .env файле")
                
            service = Service(executable_path=self.chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=self.chrome_options)
            
            # Настройка stealth режима
            stealth(self.driver,
                   languages=["en-US", "en"],
                   vendor="Google Inc.",
                   platform="Win32",
                   webgl_vendor="Intel Inc.",
                   renderer="Intel Iris OpenGL Engine",
                   fix_hairline=True,
                   )
            
            print("Веб-драйвер успешно инициализирован")
            return True
            
        except Exception as e:
            print(f"Ошибка при инициализации веб-драйвера: {e}")
            return False

    def _random_delay(self, min_delay: float = 2.0, max_delay: float = 5.0):
        """Случайная задержка между запросами"""
        time.sleep(random.uniform(min_delay, max_delay))

    def collect_brand_links(self) -> Set[str]:
        """Сбор ссылок на бренды"""
        print("Начинаем сбор ссылок на бренды...")
        brand_links = set()

        if not self.init_webdriver():
            return brand_links

        category_links = self._extract_category_links()
        for url in category_links:
            try:
                self._random_delay()  # Случайная задержка между запросами
                self.driver.get(url)
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//a[contains(text(), 'View Brand')]"))
                )
                
                elements = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'View Brand')]")
                for element in elements:
                    link = element.get_attribute('href')
                    if link not in brand_links:
                        brand_links.add(link)
                        print(f"Найдена новая ссылка на бренд: {link}")
                        
            except Exception as e:
                print(f"Ошибка при обработке {url}: {e}")
                self._random_delay(5.0, 10.0)  # Увеличенная задержка при ошибке
                continue

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
                print(f"Ошибка при обработке бренда {brand_url}: {str(e)}")

    def _extract_category_links(self) -> list:
        """Получение ссылок на категории"""
        self.driver.get("https://www.knowde.com")
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//*[starts-with(@class, 'homepage-categories_tilesList')]//a"))
        )
        
        elements = self.driver.find_elements(By.XPATH, "//*[starts-with(@class, 'homepage-categories_tilesList')]//a")
        links = []
        for element in elements:
            link = element.get_attribute('href')
            links.append(f"{link}/brands")
            # Увеличиваем пагинацию до 100 страниц для авторизованного пользователя
            for i in range(2, 101):  # Пагинация с 2 до 100
                links.append(f"{link}/brands/{i}")
            
        print(f"Собрано {len(links)} ссылок на категории с пагинацией")
        return links

    def _get_json_data_for_brand(self, brand_url: str, max_retries: int = 3) -> Optional[Dict]:
        """Получение JSON данных для бренда"""
        for attempt in range(max_retries):
            try:
                self._random_delay()  # Случайная задержка
                
                hash_value = self._get_hash_from_brand_page(brand_url)
                if not hash_value:
                    return None

                brand_path = brand_url.split('knowde.com')[1]
                json_url = f"https://www.knowde.com/_next/data/{hash_value}{brand_path}.json"

                session = requests.Session()
                session.headers.update({
                    'User-Agent': self.user_agent.random,
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Referer': 'https://www.knowde.com/',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                })
                
                response = session.get(json_url, timeout=30)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code in [403, 429]:  # Если доступ заблокирован или слишком много запросов
                    print(f"Получен статус {response.status_code}, ждем перед повторной попыткой...")
                    self._random_delay(30.0, 60.0)  # Длительная задержка при блокировке
                    
            except Exception as e:
                print(f"Попытка {attempt + 1} из {max_retries} не удалась для JSON {brand_url}: {str(e)}")
                if attempt < max_retries - 1:
                    self._random_delay(10.0, 20.0)  # Увеличенная задержка между попытками
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

    def login(self, email: str, password: str) -> bool:
        """
        Авторизация на сайте Knowde через модальные окна.
        
        Args:
            email: Email для входа
            password: Пароль
        Returns:
            bool: Успешность авторизации
        """
        try:
            if not self.init_webdriver():
                return False

            # Применяем stealth-режим
            stealth(self.driver,
                   languages=["en-US", "en"],
                   vendor="Google Inc.",
                   platform="Win32",
                   webgl_vendor="Intel Inc.",
                   renderer="Intel Iris OpenGL Engine",
                   fix_hairline=True,
                   )
            
            # Переходим на главную страницу
            self.driver.get("https://www.knowde.com")
            self._random_delay(2, 4)
            
            # Нажимаем кнопку Sign In используя data-testid
            sign_in_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='sign-in-button']"))
            )
            sign_in_button.click()
            self._random_delay(1, 2)
            
            # Ждем появления модального окна и вводим email
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR, 
                    "input[name='email'][class^='input_input']"
                ))
            )
            self._type_like_human(email_input, email)
            
            # Нажимаем Continue
            continue_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((
                    By.CSS_SELECTOR, 
                    "button[type='submit'][class^='auth-modal-continue-button']"
                ))
            )
            continue_button.click()
            self._random_delay(1, 2)
            
            # Ждем появления поля для пароля
            password_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR, 
                    "input[type='password'][class^='input_input']"
                ))
            )
            self._type_like_human(password_input, password)
            
            # Нажимаем кнопку входа
            submit_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((
                    By.CSS_SELECTOR, 
                    "button[type='submit'][class^='auth-modal-continue-button']"
                ))
            )
            submit_button.click()
            
            # Ждем успешной авторизации (проверяем наличие кнопки аккаунта)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR, 
                    "button[data-testid='account-pill']"
                ))
            )
            
            # Сохраняем cookies для дальнейшего использования
            self.cookies = self.driver.get_cookies()
            
            return True
            
        except Exception as e:
            print(f"Ошибка при авторизации: {str(e)}")
            return False

    def _type_like_human(self, element, text: str):
        """
        Эмуляция человеческого ввода текста.
        """
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))  # Случайная задержка между символами
