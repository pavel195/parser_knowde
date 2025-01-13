"""Модуль для извлечения и обработки отдельных продуктов из JSON файлов брендов."""
import json
from pathlib import Path
from typing import Dict, List, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.storage.db_storage import DBStorage
from selenium.common.exceptions import TimeoutException
import time

class ProductExtractor:
    def __init__(self, storage: DBStorage, driver=None):
        self.storage = storage
        self.driver = driver

    def extract_products_from_brand(self, brand_name: str) -> List[Dict]:
        """Извлекает все продукты из JSON файла бренда и сохраняет их отдельно."""
        print(f"Начинаем извлечение продуктов для бренда: {brand_name}")
        
        brand_data = self.storage.load_brand_data(brand_name)
        if not brand_data:
            print(f"Не найдены данные для бренда: {brand_name}")
            return []

        processed_products = []
        
        try:
            queries = brand_data['pageProps']['dehydratedState']['queries']
            print(f"Найдено {len(queries)} queries для бренда {brand_name}")
            
            # Получаем свойства бренда
            brand_properties = self._extract_brand_properties(queries)
            print(f"Извлечены свойства бренда: {brand_properties}")
            
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
                            self.storage.save_product(processed_product)
                            print(f"Обработан продукт: {processed_product['name']}")
                else:
                    print(f"Не найдено продуктов для бренда {brand_name}")
            else:
                print(f"Не найден query с продуктами для бренда {brand_name}")

            return processed_products

        except Exception as e:
            print(f"Ошибка при обработке бренда {brand_name}: {str(e)}")
            return []

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
                # Добавляем поля для таблиц и документов
                'tables': [],
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

            # Если есть драйвер, извлекаем таблицы и документы
            if self.driver:
                extracted_data = self._extract_product_tables(processed['product_url'])
                processed['tables'] = extracted_data['tables']
                processed['documents'] = extracted_data['documents']
                processed['img'] = extracted_data['img']
                processed['info'] = extracted_data['info']

            return processed

        except (KeyError, TypeError, AttributeError) as e:
            print(f"Ошибка при обработке продукта {product.get('name', 'Unknown')}: {str(e)}")
            return None

    def _extract_product_tables(self, product_url: str) -> Dict:
        """Извлекает данные из таблиц и документов на странице продукта."""
        result = {
            'tables': [],
            'documents': {},
            'img': [],
            'info': []
        }

        try:
            print(f"Загрузка страницы продукта: {product_url}")
            
            # Добавляем настройки для стабильной работы
            self.driver.set_page_load_timeout(30)
            self.driver.set_script_timeout(30)
            
            # Добавляем обработку ошибок загрузки страницы
            try:
                self.driver.get(product_url)
            except TimeoutException:
                self.driver.execute_script("window.stop();")

            # Ждем загрузки элементов
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table[class^='table-content_table']"))
            )

            
            # Извлечение таблиц из основного контента
            table_elements = self.driver.find_elements(By.CSS_SELECTOR, "table[class^='table-content_table']")
            for table in table_elements:
                # Обработка таблиц первого типа
                headers = []
                header_row = table.find_element(By.CSS_SELECTOR, "thead tr")
                header_cells = header_row.find_elements(By.CSS_SELECTOR, "td, th")
                headers = [cell.text.strip() for cell in header_cells]
                
                rows = []
                row_elements = table.find_elements(By.CSS_SELECTOR, "tbody tr")
                for row in row_elements:
                    row_data = [cell.text.strip() for cell in row.find_elements(By.CSS_SELECTOR, "td")]
                    if row_data:
                        rows.append(row_data)
                
                if headers or rows:
                    table_name = ""
                    caption = table.find_elements(By.CSS_SELECTOR, "caption")
                    if caption:
                        table_name = caption[0].text.strip()
                    
                    result['tables'].append({
                        'type': 'content',
                        'name': table_name,
                        'headers': headers,
                        'rows': rows
                    })
            # Извлечение документов
            doc_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[class^='document-list-item_container']")
            for doc in doc_elements:
                doc_text = doc.text.strip()
                if doc_text:
                    result['documents'][doc_text] = doc.get_attribute('href')

            # Извлечение таблиц из div с классом html-content
            html_content_divs = self.driver.find_elements(By.CSS_SELECTOR, "div[class^='html-content']")
            for div in html_content_divs:
                content_tables = div.find_elements(By.CSS_SELECTOR, "table")
                for table in content_tables:
                    rows = []
                    all_rows = table.find_elements(By.CSS_SELECTOR, "tr")
                    
                    # Определяем, есть ли заголовок
                    headers = []
                    first_row = all_rows[0] if all_rows else None
                    if first_row:
                        header_cells = first_row.find_elements(By.CSS_SELECTOR, "th")
                        if header_cells:
                            headers = [cell.text.strip() for cell in header_cells]
                            all_rows = all_rows[1:]  # Пропускаем первую строку, если это заголовок
                    
                    # Обработка строк
                    for row in all_rows:
                        cells = row.find_elements(By.CSS_SELECTOR, "td")
                        row_data = [cell.text.strip() for cell in cells]
                        if row_data:
                            rows.append(row_data)
                    
                    if rows:
                        result['tables'].append({
                            'type': 'html_content',
                            'headers': headers,
                            'rows': rows
                        })
                        
            # Обработка контента из div
            for div in html_content_divs:
                # Изображения с подписями
                img_elements = div.find_elements(By.CSS_SELECTOR, "img")
                if img_elements:
                    for img in img_elements:
                        img_data = {
                            'src': img.get_attribute('src'),
                            'caption': ''
                        }   
                        result['img'].append(img_data)
                    continue
                # Информационные блоки
                info_elements = div.find_elements(By.CSS_SELECTOR, "p, ul")
                for element in info_elements:
                    if element.tag_name == 'ul':
                        li_items = element.find_elements(By.CSS_SELECTOR, "li")
                        list_items = [li.text.strip() for li in li_items if li.text.strip()]
                        if list_items:
                            result['info'].append({
                                'type': 'list',
                                'content': list_items
                            })
                    elif element.tag_name == 'p':
                        p_text = element.text.strip()
                        if p_text:
                            result['info'].append({
                                'type': 'text',
                                'content': p_text
                            })

            print(f"Извлечено таблиц: {len(result['tables'])}, документов: {len(result['documents'])}, изображений: {len(result['img'])}, инфо-блоков: {len(result['info'])}")
            return result

        except Exception as e:
            print(f"Ошибка при извлечении данных для {product_url}: {str(e)}")
            return {'tables': [], 'documents': {}, 'img': [], 'info': []} 

    def run(self):
        """Основной цикл обработки"""
        while True:
            brand = self.queue.get_next_brand()
            if not brand:
                time.sleep(5)  # Ждем новые бренды
                continue
            
            try:
                print(f"Обработка бренда: {brand}")
                products = self.extract_products_from_brand(brand)
                self.storage.update_brand_status(
                    brand, 
                    'completed',
                    products_count=len(products)
                )
            except Exception as e:
                print(f"Ошибка обработки бренда {brand}: {e}")
                self.storage.update_brand_status(brand, 'failed', str(e)) 