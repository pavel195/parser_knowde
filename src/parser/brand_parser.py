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
        self.hash_value = None  # Добавляем атрибут для хранения hash

    def _random_delay(self, min_delay: float = 2.0, max_delay: float = 5.0):
        """Случайная задержка между запросами"""
        time.sleep(random.uniform(min_delay, max_delay))

    def collect_brand_links(self) -> None:
        """Сбор и обработка брендов"""
        print("Начинаем сбор и обработку брендов...")
        processed_brands = set()

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
                return

            category_links = self._extract_category_links()
            
            for url in category_links:
                try:
                    self._random_delay()
                    self.driver.get(url)
                    
                    pagination_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[class^="pagination-action_button"]')
                    numbers = [int(link.text) for link in pagination_links if link.text.isdigit()]
                    max_number = max(numbers) if numbers else 10
                    
                    # Обрабатываем каждую страницу пагинации
                    for page in range(1, max_number + 1):
                        page_url = f"{url}/{page}"
                        print(f"\nОбработка страницы {page} из {max_number}: {page_url}")
                        
                        try:
                            self.driver.get(page_url)
                            
                            # Ждем загрузки брендов на странице
                            WebDriverWait(self.driver, 10).until(
                                EC.presence_of_all_elements_located((By.XPATH, "//a[contains(text(), 'View Brand')]"))
                            )
                            
                            # Собираем все ссылки на бренды с текущей страницы
                            current_page_brands = []
                            elements = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'View Brand')]")
                            
                            for element in elements:
                                brand_url = element.get_attribute('href')
                                brand_name = brand_url.split('/')[-1]
                                
                                if brand_name not in processed_brands:
                                    current_page_brands.append((brand_name, brand_url))
                            
                            # Обрабатываем все найденные бренды на текущей странице
                            print(f"Найдено {len(current_page_brands)} новых брендов на странице {page}")
                            
                            for brand_name, brand_url in current_page_brands:
                                try:
                                    print(f"\nОбработка бренда: {brand_url}")
                                    json_data = self._get_json_data_for_brand(brand_url)
                                    
                                    if json_data:
                                        self.storage.save_brand_data(brand_name, json_data)
                                        processed_brands.add(brand_name)
                                        print(f"Бренд {brand_name} успешно обработан и сохранен")
                                    else:
                                        print(f"Не удалось получить данные для бренда {brand_name}")
                                    
                                    self._random_delay(1, 3)
                                    
                                except Exception as e:
                                    print(f"Ошибка при обработке бренда {brand_name}: {e}")
                                    self._random_delay(5.0, 10.0)
                                    continue
                            
                            print(f"Завершена обработка страницы {page}")
                            self._random_delay(2, 4)  # Задержка между страницами
                            
                        except Exception as e:
                            print(f"Ошибка при обработке страницы {page_url}: {e}")
                            self._random_delay(5.0, 10.0)
                            continue
                            
                except Exception as e:
                    print(f"Ошибка при обработке категории {url}: {e}")
                    self._random_delay(5.0, 10.0)
                    continue

            print(f"\nВсего успешно обработано брендов: {len(processed_brands)}")

        except Exception as e:
            print(f"Общая ошибка при сборе и обработке брендов: {e}")

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
                
        print(f"Собрано {len(links)} ссылок на катего��ии с пагинацией")
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
                # Получаем hash только если он еще не получен
                if not self.hash_value:
                    self.hash_value = self._get_hash_from_brand_page(brand_url)
                    if not self.hash_value:
                        print("Не удалось получить hash значение")
                        return None

                brand_path = brand_url.split('knowde.com')[1]
                json_url = f"https://www.knowde.com/_next/data/{self.hash_value}{brand_path}.json"

                response = requests.get(json_url)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code in [403, 429]:
                    print(f"Получен статус {response.status_code}, ждем перед повторной попыткой...")
                    # Если получили 403 или 429, возможно hash устарел
                    if attempt == 0:  # Пробуем получить новый hash только при первой ошибке
                        print("Пробуем обновить hash значение...")
                        self.hash_value = self._get_hash_from_brand_page(brand_url)
                    self._random_delay(5, 10)
                self._random_delay(1, 2)    
            except Exception as e:
                print(f"Попытка {attempt + 1} из {max_retries} не удалась для {brand_url}: {str(e)}")
                if attempt < max_retries - 1:
                    self._random_delay(5, 10)
                continue
                
        return None

    def _get_hash_from_brand_page(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Получение хэша со страницы бренда"""
        print("Получение нового hash значения...")
        for attempt in range(max_retries):
            try:
                self.driver.get(url)
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "script[src*='/_next/static/']"))
                )
                
                scripts = self.driver.find_elements(By.CSS_SELECTOR, "script[src*='/_next/static/']")
                for script in scripts:
                    src = script.get_attribute('src')
                    match = re.search(r'/_next/static/([a-f0-9]{40})/', src)
                    if match:
                        hash_value = match.group(1)
                        print(f"Получен новый hash: {hash_value}")
                        return hash_value
                
            except Exception as e:
                print(f"Попытка {attempt + 1} из {max_retries} не удалась для {url}: {str(e)}")
                self._random_delay(5.0, 10.0)
                continue
                
        return None

    def __del__(self):
        """Закрываем браузер при удалении объекта"""
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()
