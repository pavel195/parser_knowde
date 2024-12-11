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

        all_products = []
        
        # Получаем данные по правильному пути
        try:
            queries = brand_data.get('pageProps', {}).get('dehydratedState', {}).get('queries', [])
            if len(queries) > 1:
                most_viewed = queries[1].get('state', {}).get('data', {}).get('most_viewed_products', {}).get('data', [])
                
                if most_viewed:
                    print(f"Найдено {len(most_viewed)} продуктов в most_viewed_products для бренда {brand_name}")
                    
                    for product in most_viewed:
                        processed_product = self._process_product(product, brand_name)
                        if processed_product:
                            all_products.append(processed_product)
                            self._save_product(processed_product)
                            print(f"Обработан продукт: {processed_product['name']}")
                else:
                    print(f"Продукты не найдены для бренда {brand_name}")
            else:
                print(f"Недостаточно queries в данных бренда {brand_name}")
                
        except Exception as e:
            print(f"Ошибка при извлечении продуктов для бренда {brand_name}: {str(e)}")

        return all_products

    def _process_product(self, product: Dict, brand_name: str) -> Optional[Dict]:
        """
        Обрабатывает данные отдельного продукта.
        
        Args:
            product: Исходные данные продукта
            brand_name: Название бренда
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
                'description': product.get('description'),
                'company_name': product.get('company_name'),
                'company_slug': product.get('company_slug'),
                
                # Изображения
                'logo_url': product.get('logo_url'),
                'banner_url': product.get('banner_url'),
                
                # Свойства продукта
                'properties': {}
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

            # Добавляем документы, если есть
            if 'documents' in product:
                processed['documents'] = product['documents']

            # Добавляем дополнительные поля, если они есть
            additional_fields = [
                'manufacturer', 'specifications',
                'features', 'applications', 'certifications'
            ]
            
            for field in additional_fields:
                if field in product:
                    processed[field] = product[field]

            return processed

        except Exception as e:
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