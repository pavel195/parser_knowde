"""Задачи для обработки брендов и продуктов."""
from typing import Dict, List
from src.storage.db_storage import DBStorage
from src.processor.product_extractor import ProductExtractor

def process_brand(brand_name: str) -> Dict:
    """Задача обработки бренда"""
    storage = DBStorage()
    try:
        # Обновляем статус бренда
        storage.update_brand_status(brand_name, 'processing')
        
        # Здесь логика обработки бренда
        
        storage.update_brand_status(brand_name, 'completed')
        return {'status': 'success', 'brand': brand_name}
    except Exception as e:
        storage.update_brand_status(brand_name, 'failed', str(e))
        raise

def extract_products(brand_name: str) -> Dict:
    """Задача извлечения продуктов"""
    storage = DBStorage()
    try:
        # Проверяем, не обработан ли уже бренд
        if storage.is_brand_products_extracted(brand_name):
            return {'status': 'skipped', 'brand': brand_name, 'reason': 'already_processed'}

        # Обновляем статус
        storage.update_extraction_status(brand_name, 'processing')
        
        # Извлекаем продукты
        extractor = ProductExtractor(storage)
        products = extractor.extract_products_from_brand(brand_name)
        
        # Обновляем статус и счетчики
        storage.update_extraction_status(
            brand_name, 
            'completed',
            products_count=len(products)
        )
        
        return {
            'status': 'success',
            'brand': brand_name,
            'products_count': len(products)
        }
    except Exception as e:
        storage.update_extraction_status(brand_name, 'failed', error=str(e))
        raise 