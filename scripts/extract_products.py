"""Скрипт для извлечения продуктов из JSON файлов брендов."""
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.storage.db_storage import DBStorage
from src.processor.brand_processor import BrandProcessor
from src.service.brand_service import BrandService
from src.auth.knowde_auth import KnowdeAuth

def main():
    """Извлечение продуктов из JSON файлов брендов"""
    try:
        # Инициализируем авторизацию и получаем драйвер
        auth = KnowdeAuth()
        session = auth.login()
        
        if not session:
            print("Ошибка авторизации")
            sys.exit(1)
            
        storage = DBStorage()
        processor = BrandProcessor(storage)
        service = BrandService(storage, processor, driver=session['driver'])

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
    finally:
        # Закрываем браузер
        if 'session' in locals() and session and 'driver' in session:
            session['driver'].quit()

if __name__ == "__main__":
    main() 