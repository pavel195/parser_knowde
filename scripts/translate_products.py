"""
Скрипт для перевода сохраненных продуктов.
Читает JSON файлы из директории data/products и создает переведенные версии в data/translated_products.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from src.translator.text_translator import TextTranslator

class ProductTranslator:
    def __init__(self, input_dir: str = "data/products", output_dir: str = "data/translated_products"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.translator = TextTranslator()

    def translate_all_products(self):
        """Переводит все продукты из входной директории."""
        for brand_dir in self.input_dir.iterdir():
            if brand_dir.is_dir():
                print(f"Обработка бренда: {brand_dir.name}")
                self._process_brand_directory(brand_dir)

    def _process_brand_directory(self, brand_dir: Path):
        """Обрабатывает директорию с продуктами одного бренда."""
        output_brand_dir = self.output_dir / brand_dir.name
        output_brand_dir.mkdir(exist_ok=True)

        for product_file in brand_dir.glob("*.json"):
            try:
                print(f"Перевод продукта: {product_file.name}")
                with open(product_file, 'r', encoding='utf-8') as f:
                    product_data = json.load(f)

                translated_product = self._translate_product(product_data)
                
                output_file = output_brand_dir / product_file.name
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(translated_product, f, ensure_ascii=False, indent=4)
                
                print(f"Успешно переведен продукт: {product_file.name}")
                # Небольшая задержка чтобы не перегружать сервис переводов
                time.sleep(1)

            except Exception as e:
                print(f"Ошибка при переводе {product_file.name}: {str(e)}")

    def _translate_product(self, product: Dict) -> Dict:
        """
        Переводит данные продукта.
        
        Args:
            product: Исходные данные продукта
        Returns:
            Dict: Переведенные данные продукта
        """
        # Поля, которые не нужно переводить
        no_translate_fields = {'id', 'slug', 'uuid', 'company_name', 'company_slug', 
                             'company_id', 'product_url', 'logo_url', 'banner_url'}

        translated = product.copy()

        try:
            # Перевод основных полей
            for field in ['name', 'description']:
                if field in product and product[field]:
                    translated[field] = self.translator.translate_text(product[field])

            # Перевод свойств
            translated['properties'] = {}
            for prop_name, prop_items in product.get('properties', {}).items():
                translated_name = self.translator.translate_text(prop_name)
                translated_items = self.translator.translate_list(prop_items)
                translated['properties'][translated_name] = translated_items

            # Перевод свойств бренда
            translated['brand_properties'] = {
                key: self.translator.translate_list(values)
                for key, values in product.get('brand_properties', {}).items()
            }

            # Перевод summary
            if isinstance(product.get('summary'), dict):
                translated['summary'] = {}
                for summary_name, summary_items in product['summary'].items():
                    translated_name = self.translator.translate_text(summary_name)
                    translated_items = self.translator.translate_list(summary_items)
                    translated['summary'][translated_name] = translated_items

            # Перевод таблиц
            translated['tables'] = []
            for table in product.get('tables', []):
                translated_table = table.copy()
                if table['type'] == 'content':
                    translated_table['name'] = self.translator.translate_text(table['name'])
                    translated_table['headers'] = self.translator.translate_list(table['headers'])
                    translated_table['rows'] = [self.translator.translate_list(row) for row in table['rows']]
                elif table['type'] == 'html_content':
                    translated_table['headers'] = self.translator.translate_list(table['headers'])
                    translated_table['rows'] = [self.translator.translate_list(row) for row in table['rows']]
                translated['tables'].append(translated_table)

            # Перевод информационных блоков
            translated['info'] = []
            for info_block in product.get('info', []):
                if info_block['type'] == 'text':
                    translated['info'].append({
                        'type': 'text',
                        'content': self.translator.translate_text(info_block['content'])
                    })
                elif info_block['type'] == 'list':
                    translated['info'].append({
                        'type': 'list',
                        'content': self.translator.translate_list(info_block['content'])
                    })

            return translated

        except Exception as e:
            print(f"Ошибка при переводе продукта {product.get('name', 'Unknown')}: {str(e)}")
            return product

def main():
    translator = ProductTranslator()
    translator.translate_all_products()

if __name__ == "__main__":
    main() 