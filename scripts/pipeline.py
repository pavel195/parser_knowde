"""
Пайплайн для полной обработки данных с использованием Luigi:
1. Парсинг брендов
2. Извлечение продуктов
3. Перевод продуктов
"""
import os
import sys
import time
import luigi
from pathlib import Path
from datetime import datetime


project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.parser.brand_parser import BrandParser
from src.storage.brand_storage import BrandStorage
from src.processor.brand_processor import BrandProcessor
from src.service.brand_service import BrandService
from src.auth.knowde_auth import KnowdeAuth
from src.translator.text_translator import TextTranslator

class BrandParsingTask(luigi.Task):

    date = luigi.DateParameter(default=datetime.now())
    
    def output(self):
        # Маркерный файл, показывающий что задача выполнена
        return luigi.LocalTarget(f"data/pipeline/brand_parsed_data/{self.date}.mark")
    
    def run(self):
        try:
            storage = BrandStorage()
            auth = KnowdeAuth()
            
            # Получение сессии
            email = os.getenv('KNOWDE_EMAIL')
            password = os.getenv('KNOWDE_PASSWORD')
            session = auth.get_auth_session(email, password)
            
            if not session:
                raise Exception("Ошибка получения сессии")
            
            # Инициализация парсера с сессией
            parser = BrandParser(storage, session)
            
            # Сбор и обработка брендов
            parser.collect_brand_links()
            print(f"Собрано {len(parser.brand_links)} уникальных ссылок на бренды")
            parser.process_brands(parser.brand_links)
            
            # Создаем маркерный файл
            with self.output().open('w') as f:
                f.write(f'Brands parsed successfully at {datetime.now()}')
                
        except Exception as e:
            print(f"Ошибка при парсинге брендов: {str(e)}")
            raise

class ProductExtractionTask(luigi.Task):
    """Задача для извлечения продуктов"""
    date = luigi.DateParameter(default=datetime.now())
    
    def requires(self):
        # Зависимость от задачи парсинга брендов
        return BrandParsingTask(self.date)
    
    def output(self):
        return luigi.LocalTarget(f"data/pipeline/product_extracted_data/{self.date}.mark")
    
    def run(self):
        try:
            storage = BrandStorage()
            auth = KnowdeAuth()
            session = auth.login()
            
            if not session:
                raise Exception("Ошибка авторизации")
            
            try:
                processor = BrandProcessor(storage)
                service = BrandService(storage, processor, driver=session['driver'])
                
                # Получаем и обрабатываем бренды
                brands = service.list_available_brands()
                total_products = 0
                
                for brand_name in brands:
                    print(f"\nОбработка бренда: {brand_name}")
                    products = service.extract_brand_products(brand_name)
                    total_products += len(products)
                    print(f"Извлечено продуктов: {len(products)}")
                
                print(f"\nВсего обработано продуктов: {total_products}")
                
                # Создаем маркерный файл
                with self.output().open('w') as f:
                    f.write(f'Products extracted successfully at {datetime.now()}. Total products: {total_products}')
                    
            finally:
                if session and 'driver' in session:
                    session['driver'].quit()
                    
        except Exception as e:
            print(f"Ошибка при извлечении продуктов: {str(e)}")
            raise

class ProductTranslationTask(luigi.Task):
    """Задача для перевода продуктов"""
    date = luigi.DateParameter(default=datetime.now())
    
    def requires(self):
        # Зависимость от задачи извлечения продуктов
        return ProductExtractionTask(self.date)
    
    def output(self):
        return luigi.LocalTarget(f"data/pipeline/product_translated_data/{self.date}.mark")
    
    def run(self):
        try:
            from scripts.translate_products import ProductTranslator
            translator = ProductTranslator()
            translator.translate_all_products()
            
            # Создаем маркерный файл
            with self.output().open('w') as f:
                f.write(f'Products translated successfully at {datetime.now()}')
                
        except Exception as e:
            print(f"Ошибка при переводе продуктов: {str(e)}")
            raise

class KnowdePipeline(luigi.WrapperTask):
    """Основная задача пайплайна, объединяющая все этапы"""
    date = luigi.DateParameter(default=datetime.now())
    
    def requires(self):
        # Запускаем все задачи в правильном порядке
        return ProductTranslationTask(self.date)

if __name__ == "__main__":
    luigi.build([KnowdePipeline()], local_scheduler=True) 