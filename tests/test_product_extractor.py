"""Тестовый скрипт для извлечения продуктов из JSON файлов брендов."""
import json
from pathlib import Path
from typing import Dict, List, Optional

class TestProductExtractor:
    def __init__(self):
        """Инициализация экстрактора для тестовых данных."""
        self.test_dir = Path("test_data")
        self.brands_dir = self.test_dir / "brands"
        self.products_dir = self.test_dir / "products"
        
        # Проверяем существование директории с брендами
        if not self.brands_dir.exists():
            raise FileNotFoundError(f"Директория с брендами не найдена: {self.brands_dir}")
            
        # Создаем директорию для продуктов если её нет
        self.products_dir.mkdir(parents=True, exist_ok=True)

    def extract_products_from_brand_data(self, brand_data: Dict, brand_name: str) -> List[Dict]:
        """
        Извлекает данные о продуктах из JSON данных бренда.
        Args:
            brand_data: JSON данные бренда
            brand_name: Название бренда
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
                        'brand': brand_name,
                        'name': product.get('name'),
                        'slug': product.get('slug'),
                        'description': product.get('description'),
                        'company_name': product.get('company_name'),
                        'company_slug': product.get('company_slug'),
                        'logo_url': product.get('logo_url'),
                        'banner_url': product.get('banner_url'),
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
                            
                    products.append(processed)
                    
        except Exception as e:
            print(f"Ошибка при извлечении продуктов из бренда {brand_name}: {e}")
            
        return products

    def save_product(self, product: Dict) -> None:
        """
        Сохраняет обработанный продукт в отдельный JSON файл.
        Args:
            product: Обработанные данные продукта
        """
        if not product or 'id' not in product or 'brand' not in product:
            return

        brand_dir = self.products_dir / product['brand']
        brand_dir.mkdir(exist_ok=True)

        file_path = brand_dir / f"{product['id']}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(product, f, ensure_ascii=False, indent=4)

    def process_all_brands(self):
        """Обработка всех брендов из директории brands"""
        try:
            brand_files = list(self.brands_dir.glob('*.json'))
            if not brand_files:
                print("Бренды для обработки не найдены")
                return
                
            print(f"Найдено {len(brand_files)} файлов брендов")
            
            total_brands = 0
            total_products = 0
            failed_brands = 0
            
            for brand_file in brand_files:
                try:
                    brand_name = brand_file.stem
                    print(f"\nОбработка бренда: {brand_name}")
                    
                    # Читаем данные бренда
                    with open(brand_file, 'r', encoding='utf-8') as f:
                        brand_data = json.load(f)
                    
                    # Извлекаем и сохраняем продукты
                    products = self.extract_products_from_brand_data(brand_data, brand_name)
                    
                    if products:
                        for product in products:
                            self.save_product(product)
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
            product_files = list(self.products_dir.glob('**/*.json'))
            total_size = sum(f.stat().st_size for f in product_files)
            print(f"\nСтатистика файлов:")
            print(f"Создано файлов продуктов: {len(product_files)}")
            print(f"Общий размер данных: {total_size / 1024 / 1024:.2f} MB")
            
        except Exception as e:
            print(f"Ошибка при обработке данных: {e}")

def main():
    """Основная функция для запуска извлечения продуктов"""
    try:
        extractor = TestProductExtractor()
        extractor.process_all_brands()
        
    except FileNotFoundError as e:
        print(f"Ошибка: {e}")
        print("Убедитесь, что директория test_data/brands существует и содержит JSON файлы брендов")
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")

if __name__ == "__main__":
    main() 