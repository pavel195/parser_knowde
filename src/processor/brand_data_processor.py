from typing import List, Dict, Optional

class BrandDataProcessor:
    def search_products(self, brand_name: str, 
                       category: Optional[str] = None,
                       keyword: Optional[str] = None) -> List[Dict]:
        """
        Поиск продуктов бренда с улучшенной обработкой данных.
        Args:
            brand_name: Название бренда
            category: Фильтр по категории
            keyword: Поиск по ключевому слову
        Returns:
            List[Dict]: Список найденных продуктов
        """
        brand_data = self.storage.load_brand_data(brand_name)
        if not brand_data:
            return []
        
        # Получаем все продукты из разных секций
        all_products = []
        
        # Проверяем различные секции с продуктами
        page_props = brand_data.get('pageProps', {})
        
        # Проверяем most_viewed_products
        most_viewed = page_props.get('most_viewed_products', {}).get('data', [])
        all_products.extend(most_viewed)
        
        # Проверяем featured_products если есть
        featured = page_props.get('featured_products', {}).get('data', [])
        all_products.extend(featured)
        
        # Проверяем products если есть
        products = page_props.get('products', {}).get('data', [])
        all_products.extend(products)
        
        filtered_products = []
        
        for product in all_products:
            matches = True
            
            if category:
                category_match = False
                # Проверяем категории в разных местах структуры
                # В properties
                for prop in product.get('properties', []):
                    if prop.get('name') in ['Product Families', 'Categories', 'Applications']:
                        if category.lower() in [item.lower() for item in prop.get('items', [])]:
                            category_match = True
                            break
                
                # В categories если есть
                product_categories = [cat.lower() for cat in product.get('categories', [])]
                if category.lower() in product_categories:
                    category_match = True
                    
                matches = matches and category_match
            
            if keyword:
                keyword = keyword.lower()
                keyword_match = False
                
                # Проверяем ключевое слово в разных полях
                searchable_fields = [
                    product.get('name', ''),
                    product.get('description', ''),
                    product.get('summary', ''),
                    # Добавляем поиск по характеристикам
                    ' '.join([prop.get('name', '') for prop in product.get('properties', [])]),
                    ' '.join([item for prop in product.get('properties', []) for item in prop.get('items', [])])
                ]
                
                for field in searchable_fields:
                    if isinstance(field, str) and keyword in field.lower():
                        keyword_match = True
                        break
                        
                matches = matches and keyword_match
            
            if matches:
                filtered_products.append({
                    'id': product.get('id'),
                    'name': product.get('name'),
                    'description': product.get('description'),
                    'categories': [
                        item 
                        for prop in product.get('properties', []) 
                        if prop.get('name') in ['Product Families', 'Categories']
                        for item in prop.get('items', [])
                    ],
                    'applications': [
                        item 
                        for prop in product.get('properties', []) 
                        if prop.get('name') == 'Applications'
                        for item in prop.get('items', [])
                    ],
                    'properties': [
                        {
                            'name': prop.get('name'),
                            'items': prop.get('items', [])
                        }
                        for prop in product.get('properties', [])
                    ]
                })
        
        return filtered_products 