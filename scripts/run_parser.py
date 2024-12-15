"""Скрипт для запуска парсера брендов."""
import os
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.parser.brand_parser import BrandParser
from src.storage.brand_storage import BrandStorage

def main():
    """Основная функция для запуска парсера"""
    try:
        storage = BrandStorage()
        parser = BrandParser(storage)

        # Авторизация
        email = os.getenv('KNOWDE_EMAIL')
        password = os.getenv('KNOWDE_PASSWORD')
        
        if not parser.login(email, password):
            print("Ошибка авторизации")
            return
            
        # Сбор ссылок на бренды
        brand_links = parser.collect_brand_links()
        print(f"\nСобрано {len(brand_links)} уникальных ссылок на бренды")

        # Обработка и сохранение данных брендов
        parser.process_brands(brand_links)
        print("\nПарсинг завершен успешно")

    except Exception as e:
        print(f"Ошибка при выполнении парсера: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 