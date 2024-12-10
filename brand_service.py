"""
Сервисный слой для работы с брендами.
Объединяет функционал хранения и обработки данных.
"""

from typing import Optional, List, Dict
from brand_storage import BrandStorage
from brand_data_processor import BrandDataProcessor

class BrandService:
    def __init__(self, storage: BrandStorage, processor: BrandDataProcessor):
        """
        Инициализация сервиса.
        Args:
            storage: Экземпляр BrandStorage
            processor: Экземпляр BrandDataProcessor
        """
        self.storage = storage
        self.processor = processor

    def get_brand_data(self, brand_name: str) -> Optional[Dict]:
        """Получение данных бренда"""
        return self.storage.load_brand_data(brand_name)

    def get_brand_summary(self, brand_name: str) -> Optional[Dict]:
        """Получение сводки о бренде"""
        return self.processor.get_brand_summary(brand_name)

    def search_products(self, brand_name: str, category: Optional[str] = None, 
                       keyword: Optional[str] = None) -> List[Dict]:
        """Поиск продуктов"""
        return self.processor.search_products(brand_name, category, keyword)

    def get_brand_statistics(self, brand_name: str) -> Optional[Dict]:
        """Получение статистики бренда"""
        return self.processor.get_brand_statistics(brand_name)

    def list_available_brands(self) -> List[str]:
        """Получение списка доступных брендов"""
        return self.storage.list_brands()