"""Модуль для сбора и обработки брендов."""
from typing import List, Dict, Optional
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.storage.db_storage import DBStorage
from src.queue.task_queue import TaskQueue
import time
import json

class BrandCollector:
    def __init__(self, storage: DBStorage, queue: TaskQueue, driver: WebDriver):
        self.storage = storage
        self.queue = queue
        self.driver = driver
        self.base_url = "https://www.knowde.com/b/markets-adhesives-sealants/brands"

    def get_brands(self) -> List[Dict]:
        """Получение списка всех брендов"""
        brands = []
        page = 1
        total_pages = self._get_total_pages()
        
        print(f"Собрано {total_pages} страниц с брендами")
        
        while page <= total_pages:
            print(f"\nОбработка страницы {page} из {total_pages}: {self.base_url}/{page}")
            
            # Загружаем страницу
            self.driver.get(f"{self.base_url}/{page}")
            
            # Ждем загрузки брендов
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/stores/'][href*='/brands/']"))
            )
            
            # Получаем ссылки на бренды
            brand_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/stores/'][href*='/brands/']")
            brand_urls = [link.get_attribute('href') for link in brand_links]
            
            print(f"Найдено {len(brand_urls)} новых брендов на странице {page}")
            
            # Обрабатываем каждый бренд
            for brand_url in brand_urls:
                brand_data = self._process_brand(brand_url)
                if brand_data:
                    brands.append(brand_data)
            
            page += 1
            time.sleep(2)  # Небольшая пауза между страницами
            
        return brands

    def _get_total_pages(self) -> int:
        """Получение общего количества страниц с брендами"""
        self.driver.get(self.base_url)
        try:
            # Ждем загрузки пагинации
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='pagination']"))
            )
            
            # Получаем все элементы пагинации
            pagination = self.driver.find_elements(By.CSS_SELECTOR, "[class*='pagination'] button")
            if pagination:
                # Берем предпоследний элемент (последний обычно "Next")
                return int(pagination[-2].text)
        except Exception as e:
            print(f"Ошибка при получении количества страниц: {e}")
        return 1

    def _process_brand(self, brand_url: str) -> Optional[Dict]:
        """Обработка отдельного бренда"""
        try:
            brand_name = brand_url.split('/')[-1]
            print(f"\nОбработка бренда: {brand_url}")
            
            self.driver.get(brand_url)
            
            # Ждем загрузки данных
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "script#__NEXT_DATA__"))
            )
            
            # Получаем данные из script тега
            script = self.driver.find_element(By.CSS_SELECTOR, "script#__NEXT_DATA__")
            data = json.loads(script.get_attribute('innerHTML'))
            
            # Сохраняем данные бренда
            self.storage.save_brand_data(brand_name, data)
            
            # Добавляем в очередь на обработку продуктов
            self.queue.enqueue_brand_for_processing(brand_name)
            
            print(f"Бренд {brand_name} успешно обработан и сохранен")
            return {'name': brand_name, 'data': data}
            
        except Exception as e:
            print(f"Ошибка при обработке бренда {brand_url}: {e}")
            return None

    def process_brands(self):
        """Обработка брендов"""
        try:
            brands = self.get_brands()
            print(f"\nВсего обработано брендов: {len(brands)}")
            return brands
        except Exception as e:
            print(f"Ошибка при обработке брендов: {e}")
            raise 