import os
import json
from typing import Dict, List, Optional, Union

class BrandDataProcessor:
    def __init__(self, data_directory: str = "brand_data"):
        self.data_directory = data_directory
        
    def get_brand_summary(self, brand_name: str) -> Optional[Dict]:
        """
        Получение краткой сводки о бренде
        """
        brand_data = self._load_brand_data(brand_name)
        if not brand_data:
            return None
            
        company_info = brand_data.get('pageProps', {}).get('company', {})
        products = brand_data.get('pageProps', {}).get('products', [])
        
        return {
            'name': company_info.get('name'),
            'description': company_info.get('description'),
            'total_products': len(products),
            'categories': self._get_unique_categories(products),
            'website': company_info.get('website'),
            'location': company_info.get('location')
        }
    
    def get_product_details(self, brand_name: str, product_id: str) -> Optional[Dict]:
        """
        Получение детальной информации о продукте
        """
        brand_data = self._load_brand_data(brand_name)
        if not brand_data:
            return None
            
        products = brand_data.get('pageProps', {}).get('products', [])
        for product in products:
            if product.get('id') == product_id:
                return {
                    'id': product.get('id'),
                    'name': product.get('name'),
                    'description': product.get('description'),
                    'category': product.get('category'),
                    'specifications': product.get('specifications', {}),
                    'applications': product.get('applications', []),
                    'features': product.get('features', [])
                }
        return None
    
    def search_products(self, brand_name: str, 
                       category: Optional[str] = None,
                       keyword: Optional[str] = None) -> List[Dict]:
        """
        Поиск продуктов по категории и/или ключевому слову
        """
        brand_data = self._load_brand_data(brand_name)
        if not brand_data:
            return []
            
        products = brand_data.get('pageProps', {}).get('products', [])
        filtered_products = []
        
        for product in products:
            matches_category = True if category is None else product.get('category', '').lower() == category.lower()
            matches_keyword = True if keyword is None else keyword.lower() in product.get('name', '').lower() or \
                                                        keyword.lower() in product.get('description', '').lower()
                                                        
            if matches_category and matches_keyword:
                filtered_products.append({
                    'id': product.get('id'),
                    'name': product.get('name'),
                    'category': product.get('category'),
                    'short_description': product.get('description', '')[:100] + '...'
                })
                
        return filtered_products
    
    def get_brand_statistics(self, brand_name: str) -> Optional[Dict]:
        """
        Получение статистики по бренду
        """
        brand_data = self._load_brand_data(brand_name)
        if not brand_data:
            return None
            
        products = brand_data.get('pageProps', {}).get('products', [])
        categories = self._get_unique_categories(products)
        
        return {
            'total_products': len(products),
            'categories_count': len(categories),
            'categories_distribution': self._get_categories_distribution(products),
            'has_specifications': sum(1 for p in products if p.get('specifications')),
            'has_applications': sum(1 for p in products if p.get('applications'))
        }
    
    def _load_brand_data(self, brand_name: str) -> Optional[Dict]:
        """
        Загрузка данных бренда из JSON файла
        """
        try:
            file_path = os.path.join(self.data_directory, f"{brand_name}.json")
            if not os.path.exists(file_path):
                return None
                
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            print(f"Ошибка при загрузке данных бренда {brand_name}: {str(e)}")
            return None
    
    def _get_unique_categories(self, products: List[Dict]) -> List[str]:
        """
        Получение списка уникальных категорий
        """
        return list(set(p.get('category') for p in products if p.get('category')))
    
    def _get_categories_distribution(self, products: List[Dict]) -> Dict[str, int]:
        """
        Получение распределения продуктов по категориям
        """
        distribution = {}
        for product in products:
            category = product.get('category')
            if category:
                distribution[category] = distribution.get(category, 0) + 1
        return distribution

# Пример использования
if __name__ == "__main__":
    processor = BrandDataProcessor()
    
    # Пример работы с брендом
    brand_name = "accor"
    
    # Получение сводки о бренде
    summary = processor.get_brand_summary(brand_name)
    if summary:
        print(f"\nСводка о бренде: {brand_name}")
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    
    # Поиск продуктов по категории
    products = processor.search_products(brand_name, category="Polymers")
    if products:
        print("\nНайденные продукты в категории 'Polymers':")
        print(json.dumps(products[:3], indent=2, ensure_ascii=False))
    
    # Получение статистики
    stats = processor.get_brand_statistics(brand_name)
    if stats:
        print(f"\nСтатистика бренда:{brand_name}")
        print(json.dumps(stats, indent=2, ensure_ascii=False)) 