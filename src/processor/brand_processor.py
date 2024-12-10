"""Модуль для обработки данных брендов."""
from typing import Dict, List, Optional
from src.storage.brand_storage import BrandStorage

class BrandProcessor:
    def __init__(self, storage: BrandStorage):
        self.storage = storage

    def get_brand_summary(self, brand_name: str) -> Optional[Dict]:
        """Формирование сводки о бренде"""
        data = self.storage.load_brand_data(brand_name)
        if not data:
            return None
            
        company_info = data.get('pageProps', {})
        products = company_info.get('most_viewed_products', {}).get('data', [])
        
        return {
            'name': company_info.get('name'),
            'description': company_info.get('description'),
            'total_products': len(products),
            'categories': self._get_unique_categories(products),
            'website': company_info.get('social_links', [{}])[0].get('url'),
            'location': company_info.get('hq_address')
        }

    def search_products(self, brand_name: str, 
                       category: Optional[str] = None,
                       keyword: Optional[str] = None) -> List[Dict]:
        """Поиск продуктов"""
        # Код поиска продуктов (оставляем текущую реализацию) 