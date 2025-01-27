"""
Скрипт для перевода сохраненных продуктов.
Читает JSON файлы из директории data/products и создает переведенные версии в data/translated_products.
"""
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

import json
import time
from typing import Dict
from src.translator.text_translator import TextTranslator

class ProductTranslator:
    def __init__(self, input_dir: str = "data/products", output_dir: str = "data/translated_products"):
        """
        Перевод продуктов.
        
        Args:
            input_dir: Директория с исходными JSON файлами
            output_dir: Директория для сохранения переведенных файлов
        """
        try:
            self.input_dir = Path(input_dir)
            if not self.input_dir.exists():
                raise ValueError(f"Директория с продуктами не найдена: {input_dir}")

            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            print("Инициализация переводчика...")
            self.translator = TextTranslator()
            print("Переводчик успешно инициализирован")
            
        except Exception as e:
            print(f"Ошибка при инициализации ProductTranslator: {str(e)}")
            raise

    def translate_all_products(self):
        """Переводит все продукты из входной директории."""
        try:
            brand_dirs = [d for d in self.input_dir.iterdir() if d.is_dir()]
            total_brands = len(brand_dirs)
            print(f"\nНайдено брендов для обработки: {total_brands}")

            for brand_idx, brand_dir in enumerate(brand_dirs, 1):
                print(f"\nОбработка бренда {brand_idx}/{total_brands}: {brand_dir.name}")
                self._process_brand_directory(brand_dir)
                
        except Exception as e:
            print(f"Ошибка при переводе продуктов: {str(e)}")

    def _process_brand_directory(self, brand_dir: Path):
        """
        Обрабатывает директорию с продуктами одного бренда.
        
        Args:
            brand_dir: Путь к директории бренда
        """
        try:
            output_brand_dir = self.output_dir / brand_dir.name
            output_brand_dir.mkdir(exist_ok=True)

            product_files = list(brand_dir.glob("*.json"))
            total_products = len(product_files)
            print(f"Найдено продуктов: {total_products}")

            for idx, product_file in enumerate(product_files, 1):
                output_file = output_brand_dir / product_file.name
                
                # Пропускаем уже переведенные файлы
                if output_file.exists():
                    print(f"\nПропуск {idx}/{total_products}: {product_file.name} (уже переведен)")
                    continue

                print(f"\nПеревод продукта {idx}/{total_products}: {product_file.name}")
                
                try:
                    # Загрузка данных продукта
                    with open(product_file, 'r', encoding='utf-8') as f:
                        product_data = json.load(f)

                    # Перевод данных
                    translated_product = self.translator.translate(product_data)
                    
                    if translated_product:
                        # Сохранение результата
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(translated_product, f, ensure_ascii=False, indent=4)
                        print(f"Успешно переведен и сохранен: {product_file.name}")
                    else:
                        print(f"Ошибка: Получен пустой перевод для {product_file.name}")
                    
                    # Небольшая задержка между запросами
                    if idx < total_products:
                        time.sleep(1)

                except Exception as e:
                    print(f"Ошибка при обработке файла {product_file.name}: {str(e)}")
                    continue

        except Exception as e:
            print(f"Ошибка при обработке бренда {brand_dir.name}: {str(e)}")

def main():
    try:
        translator = ProductTranslator()
        translator.translate_all_products()
        print("\nПеревод всех продуктов завершен")
    except Exception as e:
        print(f"Критическая ошибка: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 