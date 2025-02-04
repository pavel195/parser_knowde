"""Модуль для обработки данных брендов."""
from typing import Dict, List, Optional
import json
from pathlib import Path
from src.storage.brand_storage import BrandStorage

class BrandProcessor:
    def __init__(self, storage: BrandStorage):
        self.storage = storage
        self.data_dir = Path("data")
        self.products_dir = self.data_dir / "products"

    def get_brand_summary(self, brand_name: str) -> Optional[Dict]:
        """
        Формирование сводки о бренде.
        
        Args:
            brand_name: Название бренда
            
        Returns:
            Dict: Сводка о бренде или None, если бренд не найден
        """
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
        
    def _get_unique_categories(self, products: List[Dict]) -> List[str]:
        """
        Получение уникальных категорий из списка продуктов.
        
        Args:
            products: Список продуктов
            
        Returns:
            List[str]: Список уникальных категорий
        """
        categories = set()
        for product in products:
            if 'categories' in product:
                categories.update(product['categories'])
        return sorted(list(categories))

    def search_products(self, brand_name: str, category: Optional[str] = None, 
                       keyword: Optional[str] = None) -> List[Dict]:
        """
        Поиск продуктов бренда с фильтрацией.
        
        Args:
            brand_name: Название бренда
            category: Категория для фильтрации
            keyword: Ключевое слово для поиска
            
        Returns:
            List[Dict]: Список найденных продуктов
        """
        try:
            brand_products_dir = self.products_dir / brand_name
            if not brand_products_dir.exists():
                return []

            results = []
            
            # Читаем все файлы продуктов бренда
            for product_file in brand_products_dir.glob("*.json"):
                try:
                    with open(product_file, 'r', encoding='utf-8') as f:
                        product = json.load(f)
                    
                    # Проверяем категорию
                    if category:
                        product_categories = product.get('categories', [])
                        if not product_categories or category not in product_categories:
                            continue
                    
                    # Проверяем ключевое слово
                    if keyword:
                        keyword = keyword.lower()
                        searchable_fields = [
                            product.get('name', ''),
                            product.get('description', ''),
                            product.get('summary', ''),
                            *[str(v) for v in product.get('properties', {}).values()],
                            *product.get('categories', [])
                        ]
                        
                        searchable_text = ' '.join(str(field).lower() for field in searchable_fields)
                        if keyword not in searchable_text:
                            continue
                    
                    results.append(product)
                    
                except Exception as e:
                    print(f"Ошибка при обработке файла {product_file}: {str(e)}")
                    continue
            
            return results
            
        except Exception as e:
            print(f"Ошибка при поиске продуктов бренда {brand_name}: {str(e)}")
            return []

    def get_product_details(self, brand_name: str, product_id: str) -> Optional[Dict]:
        """
        Получение детальной информации о продукте.
        
        Args:
            brand_name: Название бренда
            product_id: ID продукта
            
        Returns:
            Dict: Данные о продукте или None, если продукт не найден
        """
        try:
            product_file = self.products_dir / brand_name / f"{product_id}.json"
            if not product_file.exists():
                return None
                
            with open(product_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            print(f"Ошибка при получении данных продукта {product_id}: {str(e)}")
            return None

    def get_brand_categories(self, brand_name: str) -> List[str]:
        """
        Получение списка всех категорий бренда.
        
        Args:
            brand_name: Название бренда
            
        Returns:
            List[str]: Список категорий
        """
        try:
            categories = set()
            brand_products_dir = self.products_dir / brand_name
            
            if not brand_products_dir.exists():
                return []
                
            for product_file in brand_products_dir.glob("*.json"):
                try:
                    with open(product_file, 'r', encoding='utf-8') as f:
                        product = json.load(f)
                        categories.update(product.get('categories', []))
                except Exception:
                    continue
                    
            return sorted(list(categories))
            
        except Exception as e:
            print(f"Ошибка при получении категорий бренда {brand_name}: {str(e)}")
            return []

