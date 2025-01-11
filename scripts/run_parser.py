"""Скрипт для запуска парсера брендов."""
import os
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.parser.brand_parser import BrandParser
from src.storage.db_storage import DBStorage
from src.auth.knowde_auth import KnowdeAuth

def main():
    """Основная функция для запуска парсера"""
    try:
        storage = DBStorage()
        
        # Инициализация авторизации
        auth = KnowdeAuth()
        email = os.getenv('KNOWDE_EMAIL')
        password = os.getenv('KNOWDE_PASSWORD')
        
        # Получение сессии
        session = auth.get_auth_session(email, password)
        if not session:
            print("Ошибка получения сессии")
            return
            
        # Инициализация парсера с сессией
        parser = BrandParser(storage, session)
            
        # Сбор ссылок на бренды
        parser.collect_brand_links()
        print(f"\nСобрано {len(parser.brand_links)} уникальных ссылок на бренды")

        # Обработка и сохранение данных брендов
        parser.process_brands(parser.brand_links)
        print("\nПарсинг завершен успешно")

    except Exception as e:
        print(f"Ошибка при выполнении парсера: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 