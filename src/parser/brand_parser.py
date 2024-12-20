"""Модуль для парсинга данных о брендах."""
import os
import random
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from requests_html import HTMLSession
import re
from typing import Set, Optional, Dict
from src.storage.brand_storage import BrandStorage

class BrandParser:
    def __init__(self, storage: BrandStorage, session: Dict):
        self.storage = storage
        self.session = session
        self.driver = session['driver']  # Используем уже авторизованный драйвер

    def _random_delay(self, min_delay: float = 2.0, max_delay: float = 5.0):
        """Случайная задержка между запросами"""
        time.sleep(random.uniform(min_delay, max_delay))

    def collect_brand_links(self) -> Set[str]:
        """Сбор ссылок на бренды"""
        print("Начинаем сбор ссылок на бренды...")
        brand_links = set()

        try:
            # Проверяем авторизацию
            self.driver.get("https://www.knowde.com")
            self._random_delay(1, 2)
            
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-testid='account-pill']"))
                )
                print("Авторизация подтверждена")
            except Exception:
                print("Ошибка: Сессия не авторизована")
                return set()

            category_links = self._extract_category_links()
            #url - это ссылка на категорию .../brands
            for url in category_links:
                try:
                    self._random_delay()  # Задержка между запросами
                    self.driver.get(url) # переходим на страницу с .../brands
                    
                    pagination_links = self.driver.find_elements(By.CSS_SELECTOR,  'a[class^="pagination-action_button"]')
                    # Извлекаем числа из href ссылок и находим максимальное
                    numbers = [int(link.text) for link in pagination_links if link.text.isdigit()]
                    
                    max_number = max(numbers) if numbers else 10
                    for i in range(1, max_number + 1):
                        link = (f"{url}/{i}")
                        try:
                            self.driver.get(link)
                            # Используем XPath для поиска брендов
                            WebDriverWait(self.driver, 10).until(
                                EC.presence_of_all_elements_located((By.XPATH, "//a[contains(text(), 'View Brand')]"))
                            )
                        
                            elements = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'View Brand')]")
                            for element in elements:
                                link_brand = element.get_attribute('href')
                                if link_brand not in brand_links:
                                    brand_links.add(link_brand)
                                    print(f"Найдена новая ссылка на бренд: {link_brand}")
                        except Exception as e:
                            print(f"Ошибка при обработке {url}: {e}")
                            self._random_delay(5.0, 10.0)  # Увеличенная задержка при ошибке
                            continue
                            
                except Exception as e:
                    print(f"Ошибка при обработке {url}: {e}")
                    self._random_delay(5.0, 10.0)  # Увеличенная задержка при ошибке
                    continue

        except Exception as e:
            print(f"Ошибка при сборе ссылок: {e}")
        
        return brand_links

    def _extract_category_links(self) -> list:
        """Получение ссылок на категории"""
        self.driver.get("https://www.knowde.com")
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//*[starts-with(@class, 'homepage-categories_tilesList')]//a"))
        )
        # element - это ссылка на категорию
        elements = self.driver.find_elements(By.XPATH, "//*[starts-with(@class, 'homepage-categories_tilesList')]//a")
        links = []

        for element in elements:
            """Получение ссылок на по типу /markets-adhesives-sealants/brands/{1,2,3...}"""
            link = element.get_attribute('href')
            links.append(f"{link}/brands")
            
            # for i in range(2, 10+ 1):
            #     links.append(f"{link}/brands/{i}")
                
        print(f"Собрано {len(links)} ссылок на категории с пагинацией")
        return links

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
                    self._random_delay(1, 3)  # Задержка между брендами
                    
            except Exception as e:
                print(f"Ошибка при обработке бренда {brand_url}: {str(e)}")
                self._random_delay(5, 10)  # Увеличенная задержка при ошибке

    def _get_json_data_for_brand(self, brand_url: str, max_retries: int = 3) -> Optional[Dict]:
        """Получение JSON данных для бренда"""
        for attempt in range(max_retries):
            try:
                hash_value = self._get_hash_from_brand_page(brand_url)
                if not hash_value:
                    return None

                brand_path = brand_url.split('knowde.com')[1]
                json_url = f"https://www.knowde.com/_next/data/{hash_value}{brand_path}.json"

                # Используем куки из авторизованной сессии
                cookies = {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()}
                
                response = requests.get(
                    json_url,
                    cookies=cookies,
                    headers={
                        'User-Agent': self.session['user_agent'],
                        'Accept': 'application/json',
                        'Referer': brand_url
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code in [403, 429]:
                    print(f"Получен статус {response.status_code}, ждем перед повторной попыткой...")
                    self._random_delay(30.0, 60.0)
                    
            except Exception as e:
                print(f"Попытка {attempt + 1} из {max_retries} не удалась для {brand_url}: {str(e)}")
                if attempt < max_retries - 1:
                    self._random_delay(10.0, 20.0)
                continue
                
        return None

    def _get_hash_from_brand_page(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Получение хэша со страницы бренда"""
        for attempt in range(max_retries):
            try:
                # Используем авторизованный драйвер для получения хэша
                self.driver.get(url)
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "script[src*='/_next/static/']"))
                )
                
                scripts = self.driver.find_elements(By.CSS_SELECTOR, "script[src*='/_next/static/']")
                for script in scripts:
                    src = script.get_attribute('src')
                    match = re.search(r'/_next/static/([a-f0-9]{40})/', src)
                    if match:
                        return match.group(1)
                
            except Exception as e:
                print(f"Попытка {attempt + 1} из {max_retries} не удалась для {url}: {str(e)}")
                self._random_delay(5.0, 10.0)
                continue
                
        return None

    def __del__(self):
        """Закрываем браузер при удалении объекта"""
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()
