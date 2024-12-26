"""Модуль для извлечения и обработки отдельных продуктов из JSON файлов брендов."""
import json
from pathlib import Path
from typing import Dict, List, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.storage.brand_storage import BrandStorage

class ProductExtractor:
    def __init__(self, storage: BrandStorage, driver=None, output_dir: str = "data/products"):
        self.storage = storage
        self.driver = driver
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
                # URL продукта на Knowde
                'product_url': f"https://www.knowde.com/stores/{product.get('company_slug')}/products/{product.get('slug')}",
                # Изображения
                'logo_url': product.get('logo_url'),
                'banner_url': product.get('banner_url'),
                
                # Свойства продукта
                'properties': {},
                'brand_properties': brand_properties,
                # Добавляем поля для таблиц, ссылок и документов
                'tables': [],
                'links': {},
                'documents': {}
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

            # Если есть драйвер, извлекаем таблицы, ссылки и документы
            if self.driver:
                extracted_data = self._extract_product_tables(processed['product_url'])
                processed['tables'] = extracted_data['tables']
                processed['links'] = extracted_data['links']
                processed['documents'] = extracted_data['documents']

            return processed

        except (KeyError, TypeError, AttributeError) as e:
            print(f"Ошибка при обработке продукта {product.get('name', 'Unknown')}: {str(e)}")
            return None

    def _extract_product_tables(self, product_url: str) -> Dict:
        """
        Извлекает структурированные данные из таблиц и ссылок на странице продукта.
        
        Args:
            product_url: URL страницы продукта
        Returns:
            Dict: Словарь с таблицами и ссылками
        """
        result = {
            'tables': [],
            'links': {},
            'documents': {}
        }
        
        try:
            print(f"Загрузка страницы продукта: {product_url}")
            self.driver.get(product_url)
            
            # Ждем загрузки таблиц
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table[class^='table-content_table']"))
            )
            
            # Получаем все таблицы
            table_elements = self.driver.find_elements(By.CSS_SELECTOR, "table[class^='table-content_table']")
            
            for table in table_elements:
                # Извлекаем заголовки из первой строки thead
                headers = []
                header_row = table.find_element(By.CSS_SELECTOR, "thead tr")
                header_cells = header_row.find_elements(By.CSS_SELECTOR, "td")
                for cell in header_cells:
                    headers.append(cell.text.strip())
                
                # Если заголовки не найдены через td, пробуем через th
                if not headers:
                    header_cells = header_row.find_elements(By.CSS_SELECTOR, "th")
                    for cell in header_cells:
                        headers.append(cell.text.strip())
                
                # Извлекаем строки данных
                rows = []
                row_elements = table.find_elements(By.CSS_SELECTOR, "tbody tr")
                for row in row_elements:
                    row_data = []
                    cells = row.find_elements(By.CSS_SELECTOR, "td")
                    for cell in cells:
                        row_data.append(cell.text.strip())
                    if row_data:  # Добавляем только непустые строки
                        rows.append(row_data)
                
                # Добавляем структурированные данные таблицы
                if headers or rows:
                    table_name = ""
                    # Пытаемся найти название таблицы в caption
                    caption = table.find_elements(By.CSS_SELECTOR, "caption")
                    if caption:
                        table_name = caption[0].text.strip()
                    
                    result['tables'].append({
                        'name': table_name,
                        'headers': headers,
                        'rows': rows
                    })
            
            # Получаем все ссылки product-details
            link_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[class^='product-details_link']")
            for link in link_elements:
                link_text = link.text.strip()
                if link_text:  # Сохраняем только ссылки с непустым текстом
                    result['links'][link_text] = link.get_attribute('href')

            # Получаем все ссылки на документы
            doc_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[class^='document-list-item_container']")
            for doc in doc_elements:
                doc_text = doc.text.strip()
                if doc_text:  # Сохраняем только ссылки с непустым текстом
                    result['documents'][doc_text] = doc.get_attribute('href')
                
            print(f"Извлечено таблиц: {len(result['tables'])}, ссылок: {len(result['links'])}, документов: {len(result['documents'])}")
            return result
            
        except Exception as e:
            print(f"Ошибка при извлечении данных для {product_url}: {str(e)}")
            return {'tables': [], 'links': {}, 'documents': {}}

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