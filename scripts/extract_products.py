"""Скрипт для извлечения продуктов из JSON файлов брендов."""
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.storage.brand_storage import BrandStorage
from src.processor.brand_processor import BrandProcessor
from src.service.brand_service import BrandService

def main():
    """Извлечение продуктов из JSON файлов брендов"""
    try:
        storage = BrandStorage()
        processor = BrandProcessor(storage)
        service = BrandService(storage, processor)

        # Получаем список всех брендов
        brands = service.list_available_brands()
        
        total_products = 0
        for brand_name in brands:
            print(f"\nОбработка бренда: {brand_name}")
            products = service.extract_brand_products(brand_name)
            print(f"Извлечено продуктов: {len(products)}")
            total_products += len(products)

        print(f"\nВсего обработано продуктов: {total_products}")

    except Exception as e:
        print(f"Ошибка при извлечении продуктов: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 