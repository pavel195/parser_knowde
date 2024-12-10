"""
Главный модуль приложения.
Координирует работу всех компонентов системы.
"""

from brand_storage import BrandStorage
from brand_data_processor import BrandDataProcessor
from brand_service import BrandService
from combined_brands_parser import BrandParser
import json

def main():
    """
    Основная функция приложения:
    1. Инициализирует компоненты
    2. Запускает сбор данных
    3. Выполняет анализ собранных данных
    """
    # Инициализация компонентов
    storage = BrandStorage()
    processor = BrandDataProcessor(storage)
    service = BrandService(storage, processor)
    parser = BrandParser(storage)

    # Сбор данных
    print("Начинаем сбор ссылок на бренды...")
    brand_links = parser.collect_unique_brand_links()
    
    print("\nНачинаем сбор данных о брендах...")
    parser.process_brand_data(brand_links)

    # Анализ собранных данных
    print("\nАнализ собранных данных:")
    brands = service.list_available_brands()
    for brand_name in brands:
        print(f"\nАнализ бренда: {brand_name}")
        
        summary = service.get_brand_summary(brand_name)
        if summary:
            print("Сводка о бренде:")
            print(json.dumps(summary, indent=2, ensure_ascii=False))
            
        statistics = service.get_brand_statistics(brand_name)
        if statistics:
            print("\nСтатистика бренда:")
            print(json.dumps(statistics, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main() 