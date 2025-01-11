"""Сервисный слой для работы с брендами."""
from typing import Dict, List, Optional
from selenium.webdriver.remote.webdriver import WebDriver
from src.storage.db_storage import DBStorage
from src.processor.brand_processor import BrandProcessor
from src.processor.product_extractor import ProductExtractor

class BrandService:
    def __init__(self, storage: DBStorage, processor: BrandProcessor, driver: Optional[WebDriver] = None):
        self.storage = storage
        self.processor = processor
        self.product_extractor = ProductExtractor(storage, driver=driver)

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
        return self.storage.list_cbrands()

    def extract_brand_products(self, brand_name: str) -> List[Dict]:
        """
        Извлекает все продукты бренда в отдельные файлы.
        
        Args:
            brand_name: Название бренда
        Returns:
            List[Dict]: Список обработанных продуктов
        """
        return self.product_extractor.extract_products_from_brand(brand_name) 