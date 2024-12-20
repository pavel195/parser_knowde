"""Тестирование парсера с ограниченным набором данных"""
import os
import sys
from pathlib import Path
import json
from typing import Set

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.parser.brand_parser import BrandParser
from src.storage.brand_storage import BrandStorage
from src.auth.knowde_auth import KnowdeAuth
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

def test_parser(limit: int = 100):
    """
    Тест парсера с ограничением количества брендов
    Args:
        limit: Максимальное количество брендов для тестирования
    """
    # Создаем тестовую директорию
    test_dir = Path("test_data")
    test_dir.mkdir(exist_ok=True)
    
    # Инициализируем хранилище для тестовых данных
    storage = BrandStorage(data_dir=str(test_dir))
    
    try:
        # Авторизация
        print("Начинаем авторизацию...")
        auth = KnowdeAuth()
        session = auth.get_auth_session(
            os.getenv('KNOWDE_EMAIL'),
            os.getenv('KNOWDE_PASSWORD')
        )
        
        if not session:
            print("Ошибка авторизации")
            return
            
        print("Авторизация успешна")
        
        # Инициализируем парсер
        parser = BrandParser(storage, session)
        brand_links = set()
        
        print(f"\nСобираем первые {limit} ссылок на бренды...")
        
        # Получаем категории
        category_links = parser._extract_category_links()
        
        # Собираем ссылки на бренды до достижения лимита
        for category_url in category_links:
            if len(brand_links) >= limit:
                break
                
            try:
                parser.driver.get(category_url)
                WebDriverWait(parser.driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//a[contains(text(), 'View Brand')]"))
                )
                
                elements = parser.driver.find_elements(By.XPATH, "//a[contains(text(), 'View Brand')]")
                for element in elements:
                    if len(brand_links) >= limit:
                        break
                        
                    link = element.get_attribute('href')
                    if link and link not in brand_links:
                        brand_links.add(link)
                        print(f"Найдена ссылка {len(brand_links)}/{limit}: {link}")
                        
            except Exception as e:
                print(f"Ошибка при обработке категории {category_url}: {e}")
                continue
        
        print(f"\nНайдено {len(brand_links)} ссылок на бренды")
        
        # Получаем и сохраняем JSON данные
        print("\nПолучаем JSON данные брендов...")
        successful = 0
        failed = 0
        
        for brand_url in brand_links:
            try:
                print(f"\nОбработка бренда {successful + failed + 1}/{len(brand_links)}: {brand_url}")
                json_data = parser._get_json_data_for_brand(brand_url)
                
                if json_data:
                    brand_name = brand_url.split('/')[-1]
                    storage.save_brand_data(brand_name, json_data)
                    successful += 1
                    print("Данные сохранены успешно")
                else:
                    failed += 1
                    print("Не удалось получить данные")
                    
                parser._random_delay(1, 3)
                
            except Exception as e:
                failed += 1
                print(f"Ошибка при обработке бренда: {e}")
                parser._random_delay(5, 10)
        
        # Выводим статистику
        print("\nРезультаты тестирования:")
        print(f"Всего брендов обработано: {successful + failed}")
        print(f"Успешно: {successful}")
        print(f"Ошибок: {failed}")
        
        # Проверяем сохраненные файлы
        files = list(test_dir.glob('*.json'))
        total_size = sum(f.stat().st_size for f in files)
        print(f"Сохранено файлов: {len(files)}")
        print(f"Общий размер данных: {total_size / 1024 / 1024:.2f} MB")
        
    except Exception as e:
        print(f"Ошибка при выполнении теста: {e}")
    finally:
        if 'parser' in locals() and hasattr(parser, 'driver'):
            parser.driver.quit()

if __name__ == "__main__":
    test_parser(limit=100) 