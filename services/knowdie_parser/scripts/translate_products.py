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
from tqdm import tqdm
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
            
            
            self.log_dir = Path("data/logs/translation")
            self.log_dir.mkdir(parents=True, exist_ok=True)
            
            print("Инициализация переводчика...")
            self.translator = TextTranslator()
            print("Переводчик успешно инициализирован")
            
        except Exception as e:
            print(f"Ошибка при инициализации ProductTranslator: {str(e)}")
            raise

    def _save_error_log(self, brand: str, product_file: str, error: str):
        """Сохраняет информацию об ошибках перевода"""
        log_file = self.log_dir / f"translation_errors_{time.strftime('%Y%m%d')}.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {brand} | {product_file} | {error}\n")

    def translate_all_products(self):
        """Переводит все продукты из входной директории."""
        try:
            brand_dirs = [d for d in self.input_dir.iterdir() if d.is_dir()]
            total_brands = len(brand_dirs)
            print(f"\nНайдено брендов для обработки: {total_brands}")

            total_products = 0
            translated_products = 0
            skipped_products = 0
            failed_products = 0

            for brand_idx, brand_dir in enumerate(brand_dirs, 1):
                print(f"\nОбработка бренда {brand_idx}/{total_brands}: {brand_dir.name}")
                stats = self._process_brand_directory(brand_dir)
                
                total_products += stats['total']
                translated_products += stats['translated']
                skipped_products += stats['skipped']
                failed_products += stats['failed']

            print("\nИтоги обработки:")
            print(f"Всего продуктов: {total_products}")
            print(f"Успешно переведено: {translated_products}")
            print(f"Пропущено (уже переведены): {skipped_products}")
            print(f"Не удалось перевести: {failed_products}")
                
        except Exception as e:
            print(f"Ошибка при переводе продуктов: {str(e)}")

    def _process_brand_directory(self, brand_dir: Path) -> Dict[str, int]:
        """
        Обрабатывает директорию с продуктами одного бренда.
        
        Args:
            brand_dir: Путь к директории бренда
        Returns:
            Dict[str, int]: Статистика обработки
        """
        stats = {
            'total': 0,
            'translated': 0,
            'skipped': 0,
            'failed': 0
        }

        try:
            output_brand_dir = self.output_dir / brand_dir.name
            output_brand_dir.mkdir(exist_ok=True)

            product_files = list(brand_dir.glob("*.json"))
            stats['total'] = len(product_files)
            
            if not product_files:
                print(f"Продукты не найдены в директории: {brand_dir}")
                return stats

            print(f"Найдено продуктов: {len(product_files)}")
            
            
            with tqdm(total=len(product_files), desc=f"Перевод {brand_dir.name}") as pbar:
                for product_file in product_files:
                    output_file = output_brand_dir / product_file.name
                    
                   
                    if output_file.exists():
                        stats['skipped'] += 1
                        pbar.update(1)
                        continue

                    try:
                        
                        with open(product_file, 'r', encoding='utf-8') as f:
                            product_data = json.load(f)

                       
                        translated_product = self.translator.translate(product_data)
                        
                        if translated_product:
                            
                            with open(output_file, 'w', encoding='utf-8') as f:
                                json.dump(translated_product, f, ensure_ascii=False, indent=4)
                            stats['translated'] += 1
                        else:
                            raise ValueError("Получен пустой перевод")

                    except Exception as e:
                        stats['failed'] += 1
                        self._save_error_log(brand_dir.name, product_file.name, str(e))
                        print(f"\nОшибка при обработке файла {product_file.name}: {str(e)}")
                        continue
                    finally:
                        pbar.update(1)
                        
                        time.sleep(1)

        except Exception as e:
            print(f"Ошибка при обработке бренда {brand_dir.name}: {str(e)}")
            self._save_error_log(brand_dir.name, "BRAND_LEVEL", str(e))

        return stats

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