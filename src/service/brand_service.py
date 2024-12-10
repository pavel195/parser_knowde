"""Сервисный слой для работы с брендами."""
from typing import Dict, List, Optional
from src.storage.brand_storage import BrandStorage
from src.processor.brand_processor import BrandProcessor

class BrandService:
    def __init__(self, storage: BrandStorage, processor: BrandProcessor):
        self.storage = storage
        self.processor = processor

    def get_brand_data(self, brand_name: str, include_products: bool = False) -> Optional[Dict]:
        """Получение данных бренда"""
        data = self.storage.load_brand_data(brand_name)
        if data and not include_products:
            data['pageProps'].pop('most_viewed_products', None)
        return data

    def get_brand_summary(self, brand_name: str) -> Optional[Dict]:
        """Получение сводки о бренде"""
        return self.processor.get_brand_summary(brand_name)

    def search_products(self, brand_name: str, category: Optional[str] = None, 
                       keyword: Optional[str] = None) -> List[Dict]:
        """Поиск продуктов"""
        return self.processor.search_products(brand_name, category, keyword)

    def list_available_brands(self) -> List[str]:
        """Получение списка брендов"""
        return self.storage.list_brands() 