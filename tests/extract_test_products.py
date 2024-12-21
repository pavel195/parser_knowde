"""Скрипт для извлечения продуктов из тестовых JSON файлов брендов."""
import json
from pathlib import Path
from typing import Dict, List

def extract_products_from_brand_data(brand_data: Dict) -> List[Dict]:
    """
    Извлекает данные о продуктах из JSON данных бренда.
    Args:
        brand_data: JSON данные бренда
    Returns:
        List[Dict]: Список обработанных продуктов
    """
    products = []
    
    try:
        # Получаем данные по правильному пути
        page_props = brand_data.get('pageProps', {})
        
        # Проверяем различные секции с продуктами
        sections = [
            page_props.get('most_viewed_products', {}).get('data', []),
            page_props.get('featured_products', {}).get('data', []),
            page_props.get('products', {}).get('data', [])
        ]
        
        for section in sections:
            for product in section:
                processed = {
                    'id': product.get('id'),
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

                # Добавляем дополнительные поля
                additional_fields = [
                    'manufacturer', 'specifications',
                    'features', 'applications', 'certifications'
                ]
                
                for field in additional_fields:
                    if field in product:
                        processed[field] = product[field]
                        
                products.append(processed)
                
    except Exception as e:
        print(f"Ошибка при извлечении продуктов: {e}")
        
    return products

def process_test_data():
    """Обработка тестовых данных и извлечение продуктов"""
    # Пути к директориям
    test_dir = Path("test_data")
    products_dir = test_dir / "products"
    products_dir.mkdir(exist_ok=True)
    
    if not test_dir.exists():
        print("Директория test_data не найдена")
        return
        
    try:
        # Счетчики для статистики
        total_brands = 0
        total_products = 0
        failed_brands = 0
        
        # Обрабатываем каждый JSON файл бренда
        for brand_file in test_dir.glob("*.json"):
            try:
                brand_name = brand_file.stem
                print(f"\nОбработка бренда: {brand_name}")
                
                # Читаем данные бренда
                with open(brand_file, 'r', encoding='utf-8') as f:
                    brand_data = json.load(f)
                
                # Извлекаем продукты
                products = extract_products_from_brand_data(brand_data)
                
                if products:
                    # Создаем директорию для продуктов бренда
                    brand_products_dir = products_dir / brand_name
                    brand_products_dir.mkdir(exist_ok=True)
                    
                    # Сохраняем каждый продукт в отдельный файл
                    for product in products:
                        if product.get('id'):
                            product_file = brand_products_dir / f"{product['id']}.json"
                            with open(product_file, 'w', encoding='utf-8') as f:
                                json.dump(product, f, ensure_ascii=False, indent=4)
                            total_products += 1
                    
                    print(f"Извлечено продуктов: {len(products)}")
                    total_brands += 1
                else:
                    print("Продукты не найдены")
                    failed_brands += 1
                    
            except Exception as e:
                print(f"Ошибка при обработке бренда {brand_file.name}: {e}")
                failed_brands += 1
                continue
        
        # Выводим итоговую статистику
        print("\nРезультаты обработки:")
        print(f"Обработано брендов: {total_brands}")
        print(f"Ошибок обработки: {failed_brands}")
        print(f"Всего извлечено продуктов: {total_products}")
        
        # Проверяем размер файлов
        product_files = list(products_dir.glob('**/*.json'))
        total_size = sum(f.stat().st_size for f in product_files)
        print(f"\nСтатистика файлов:")
        print(f"Создано файлов продуктов: {len(product_files)}")
        print(f"Общий размер данных: {total_size / 1024 / 1024:.2f} MB")
        
    except Exception as e:
        print(f"Ошибка при обработке данных: {e}")

if __name__ == "__main__":
    process_test_data() 