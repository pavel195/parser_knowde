"""Модуль для извлечения и обработки отдельных продуктов из JSON файлов брендов."""
import json
from pathlib import Path
from typing import Dict, List, Optional
from src.storage.brand_storage import BrandStorage

class ProductExtractor:
    def __init__(self, storage: BrandStorage, output_dir: str = "data/products"):
        self.storage = storage
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_products_from_brand(self, brand_name: str) -> List[Dict]:
        """
        Извлекает все продукты из JSON файла бренда и сохраняет их отдельно.
        
        Args:
            brand_name: Название бренда
        Returns:
            List[Dict]: Список обработанных продуктов
        """
        brand_data = self.storage.load_brand_data(brand_name)
        if not brand_data:
            return []

        processed_products = []
        
        try:
            queries = brand_data['pageProps']['dehydratedState']['queries']
            
            # Получаем свойства бренда
            brand_properties = self._extract_brand_properties(queries)
            
            # Ищем нужный query с продуктами
            products_query = None
            for query in queries:
                if 'state' in query and 'data' in query['state']:
                    if 'products' in query['state']['data']:
                        products_query = query
                        break
            
            if products_query and 'data' in products_query['state']['data']['products']:
                all_products = products_query['state']['data']['products']['data']
                
                if all_products:
                    print(f"Найдено {len(all_products)} продуктов для бренда {brand_name}")
                    
                    for product in all_products:
                        processed_product = self._process_product(product, brand_name, brand_properties)
                        if processed_product:
                            processed_products.append(processed_product)
                            self._save_product(processed_product)
                            print(f"Обработан продукт: {processed_product['name']}")
                else:
                    print(f"Продукты не найдены для бренда {brand_name}")
            else:
                print(f"Структура данных продуктов не найдена для бренда {brand_name}")
                
        except Exception as e:
            print(f"Ошибка при извлечении продуктов для бренда {brand_name}: {str(e)}")

        return processed_products

    def _extract_brand_properties(self, queries: List[Dict]) -> Dict:
        """Извлекает свойства из блоков бренда."""
        brand_properties = {}
        
        try:
            for query in queries:
                if 'state' in query and 'data' in query['state']:
                    data = query['state']['data']
                    if 'details' in data:
                        for section in data['details']:
                            for block in section.get('content_blocks', []):
                                key = block.get('key')
                                if key:
                                    if block.get('type') == 'ContentBlockType.FiltersContentBlock':
                                        brand_properties[key] = [
                                            f.get('filter_name') for f in block.get('filters', [])
                                            if f.get('filter_name')
                                        ]
                                    elif block.get('type') == 'ContentBlockType.GroupFilterContentBlock':
                                        values = []
                                        for group in block.get('group_filters', []):
                                            if 'header_filter' in group:
                                                values.append(group['header_filter'].get('filter_name'))
                                            for f in group.get('filters', []):
                                                values.append(f.get('filter_name'))
                                        brand_properties[key] = [v for v in values if v]
        except (KeyError, TypeError, AttributeError) as e:
            print(f"Ошибка при извлечении свойств бренда: {str(e)}")
        
        return brand_properties

    def _process_product(self, product: Dict, brand_name: str, brand_properties: Dict) -> Optional[Dict]:
        """
        Обрабатывает данные отдельного продукта.
        
        Args:
            product: Исходные данные продукта
            brand_name: Название бренда
            brand_properties: Свойства бренда
        Returns:
            Dict: Обработанные данные продукта
        """
        if not product:
            return None

        try:
            processed = {
                'id': product.get('id'),
                'brand': brand_name,
                'name': product.get('name'),
                'slug': product.get('slug'),
                'uuid': product.get('uuid'),
                'description': product.get('description'),
                'company_name': product.get('company_name'),
                'company_slug': product.get('company_slug'),
                'company_id': product.get('company_id'),
                'summary': product.get('summary'),
                # Изображения
                'logo_url': product.get('logo_url'),
                'banner_url': product.get('banner_url'),
                
                # Свойства продукта
                'properties': {},
                'brand_properties': brand_properties
            }
            
            # Обработка properties
            for prop in product.get('properties', []):
                prop_name = prop.get('name', '')
                prop_items = prop.get('items', [])
                processed['properties'][prop_name] = prop_items

            # Обработка summary если есть
            if 'summary' in product:
                processed['summary'] = {}
                for summary_item in product.get('summary', []):
                    summary_name = summary_item.get('name', '')
                    summary_items = summary_item.get('items', [])
                    processed['summary'][summary_name] = summary_items

            return processed

        except (KeyError, TypeError, AttributeError) as e:
            print(f"Ошибка при обработке продукта {product.get('name', 'Unknown')}: {str(e)}")
            return None

    def _save_product(self, product: Dict) -> None:
        """
        Сохраняет обработанный продукт в отдельный JSON файл.
        
        Args:
            product: Обработанные данные продукта
        """
        if not product or 'id' not in product:
            return

        brand_dir = self.output_dir / product['brand']
        brand_dir.mkdir(exist_ok=True)

        file_path = brand_dir / f"{product['id']}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(product, f, ensure_ascii=False, indent=4) 