"""
Модуль для обработки и анализа данных брендов.
Предоставляет методы для получения сводной информации и статистики.
"""

import os
import json
from typing import Dict, List, Optional, Union

class BrandDataProcessor:
    def __init__(self, storage):
        """
        Инициализация процессора данных.
        Args:
            storage: Экземпляр BrandStorage для доступа к данным
        """
        self.storage = storage
        
    def get_brand_summary(self, brand_name: str) -> Optional[Dict]:
        """
        Формирование краткой сводки о бренде.
        Args:
            brand_name: Название бренда
        Returns:
            Dict: Сводная информация о бренде или None
        """
        brand_data = self.storage.load_brand_data(brand_name)
        if not brand_data:
            return None
            
        # Получаем основную информацию о компании
        company_info = brand_data.get('pageProps', {})
        products = company_info.get('most_viewed_products', {}).get('data', [])
        
        return {
            'name': company_info.get('name'),
            'description': company_info.get('description'),
            'total_products': len(products),
            'categories': self._get_unique_categories(products),
            'website': company_info.get('social_links', [{}])[0].get('url'),
            'location': company_info.get('hq_address')
        }
    
    def get_product_details(self, brand_name: str, product_id: str) -> Optional[Dict]:
        """
        Получение детальной информации о продукте
        """
        brand_data = self.storage.load_brand_data(brand_name)
        if not brand_data:
            return None
            
        products = brand_data.get('pageProps', {}).get('most_viewed_products', {}).get('data', [])
        for product in products:
            if str(product.get('id')) == product_id:
                return {
                    'id': product.get('id'),
                    'name': product.get('name'),
                    'description': product.get('description'),
                    'properties': product.get('properties', []),
                    'summary': product.get('summary', [])
                }
        return None
    
    def search_products(self, brand_name: str, 
                       category: Optional[str] = None,
                       keyword: Optional[str] = None) -> List[Dict]:
        """
        Поиск продуктов по категории и/или ключевому слову
        """
        brand_data = self.storage.load_brand_data(brand_name)
        if not brand_data:
            return []
            
        products = brand_data.get('pageProps', {}).get('most_viewed_products', {}).get('data', [])
        filtered_products = []
        
        for product in products:
            matches_category = True
            if category:
                product_categories = []
                for prop in product.get('properties', []):
                    if prop.get('name') == 'Product Families':
                        product_categories.extend(prop.get('items', []))
                matches_category = category in product_categories
                
            matches_keyword = True
            if keyword:
                keyword = keyword.lower()
                matches_keyword = (
                    keyword in product.get('name', '').lower() or
                    keyword in product.get('description', '').lower()
                )
                
            if matches_category and matches_keyword:
                filtered_products.append({
                    'id': product.get('id'),
                    'name': product.get('name'),
                    'short_description': product.get('description', '')[:100] + '...' if product.get('description') else '',
                    'categories': [prop.get('items', []) for prop in product.get('properties', []) if prop.get('name') == 'Product Families'][0] if product.get('properties') else []
                })
                
        return filtered_products
    
    def get_brand_statistics(self, brand_name: str) -> Optional[Dict]:
        """
        Получение статистики по бренду
        """
        brand_data = self.storage.load_brand_data(brand_name)
        if not brand_data:
            return None
            
        products = brand_data.get('pageProps', {}).get('most_viewed_products', {}).get('data', [])
        
        # Собираем категории
        categories = set()
        categories_distribution = {}
        
        for product in products:
            for prop in product.get('properties', []):
                if prop.get('name') == 'Product Families':
                    for category in prop.get('items', []):
                        categories.add(category)
                        categories_distribution[category] = categories_distribution.get(category, 0) + 1
        
        return {
            'total_products': len(products),
            'categories_count': len(categories),
            'categories_distribution': categories_distribution,
            'has_specifications': sum(1 for p in products if any(s.get('name') == 'Features' for s in p.get('summary', []))),
            'has_applications': sum(1 for p in products if any(prop.get('name') == 'Applications' for prop in p.get('properties', [])))
        }
    
    def _get_unique_categories(self, products: List[Dict]) -> List[str]:
        """
        Получение списка уникальных категорий
        """
        categories = set()
        for product in products:
            for prop in product.get('properties', []):
                if prop.get('name') == 'Product Families':
                    categories.update(prop.get('items', []))
        return list(categories)