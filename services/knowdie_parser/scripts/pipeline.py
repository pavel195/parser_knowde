"""
Пайплайн для обработки данных с использованием Luigi:
1. Парсинг и сохранение брендов
2. Извлечение продуктов из сохраненных брендов
"""
import os
import sys
import luigi
from pathlib import Path
from datetime import datetime
import json
import logging
from logging.handlers import RotatingFileHandler

# Настройка путей
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Базовые пути проекта
DATA_DIR = project_root / "data"
BRAND_DATA_DIR = DATA_DIR / "brand_data"
PRODUCTS_DIR = DATA_DIR / "products"
PIPELINE_DIR = DATA_DIR / "pipeline"
LOGS_DIR = DATA_DIR / "logs"

# Создаем все необходимые директории
for directory in [DATA_DIR, BRAND_DATA_DIR, PRODUCTS_DIR, PIPELINE_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Настройка логирования
log_file = LOGS_DIR / "pipeline.log"
max_bytes = 1024 * 1024 * 1024  # 1 GB
backup_count = 5  # Количество файлов бэкапа


formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')


file_handler = RotatingFileHandler(
    log_file,
    maxBytes=max_bytes,
    backupCount=backup_count,
    encoding='utf-8'
)
file_handler.setFormatter(formatter)


console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)


logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

from src.parser.brand_parser import BrandParser
from src.storage.brand_storage import BrandStorage
from src.processor.brand_processor import BrandProcessor
from src.service.brand_service import BrandService
from src.auth.knowde_auth import KnowdeAuth
from src.database.db import init_db


logger.info("Инициализация базы данных...")
init_db()
logger.info("База данных инициализирована")

class SaveBrandTask(luigi.Task):
    """Задача для парсинга и сохранения данных бренда"""
    date = luigi.DateParameter(default=datetime.now())
    brand_url = luigi.Parameter()
    brand_name = luigi.Parameter()
    
    def output(self):
        return luigi.LocalTarget(str(BRAND_DATA_DIR / f"{self.brand_name}.json"))
    
    def run(self):
        try:
            storage = BrandStorage()
            processor = BrandProcessor(storage)
            auth = KnowdeAuth()
            
            logger.info(f"Начало сохранения бренда: {self.brand_name}")
            processor.save_pipeline_progress(self.brand_name, "processing")
            
            email = os.getenv('KNOWDE_EMAIL')
            password = os.getenv('KNOWDE_PASSWORD')
            
            if not email or not password:
                error_msg = "Не заданы учетные данные KNOWDE_EMAIL и KNOWDE_PASSWORD"
                processor.save_pipeline_progress(self.brand_name, "failed", error_msg)
                raise Exception(error_msg)
            
            logger.info("Получение авторизованной сессии...")
            session = auth.get_auth_session(email, password)
            
            if not session:
                error_msg = "Ошибка получения сессии"
                processor.save_pipeline_progress(self.brand_name, "failed", error_msg)
                raise Exception(error_msg)
            
            try:
                parser = BrandParser(storage, session)
                logger.info(f"Парсинг бренда: {self.brand_name} ({self.brand_url})")
                json_data = parser._get_json_data_for_brand(self.brand_url)
                
                if json_data:
                    storage.save_brand_data(self.brand_name, json_data)
                    processor.save_pipeline_progress(self.brand_name, "completed")
                    logger.info(f"Бренд {self.brand_name} успешно сохранен")
                else:
                    error_msg = f"Не удалось получить данные для бренда {self.brand_name}"
                    processor.save_pipeline_progress(self.brand_name, "failed", error_msg)
                    raise Exception(error_msg)
                
            finally:
                if session and 'driver' in session:
                    session['driver'].quit()
                    
        except Exception as e:
            error_msg = f"Ошибка при сохранении бренда {self.brand_name}: {str(e)}"
            logger.error(error_msg)
            processor.save_pipeline_progress(self.brand_name, "failed", str(e))
            raise

class ExtractProductsTask(luigi.Task):
    """Задача для извлечения продуктов из сохраненного бренда"""
    date = luigi.DateParameter(default=datetime.now())
    brand_url = luigi.Parameter()
    brand_name = luigi.Parameter()
    
    def requires(self):
        return SaveBrandTask(
            date=self.date,
            brand_url=self.brand_url,
            brand_name=self.brand_name
        )
    
    def output(self):
        return luigi.LocalTarget(str(PRODUCTS_DIR / f"{self.brand_name}_products.json"))
    
    def run(self):
        try:
            storage = BrandStorage()
            processor = BrandProcessor(storage)
            auth = KnowdeAuth()
            
            logger.info(f"Начало извлечения продуктов для бренда: {self.brand_name}")
            processor.save_pipeline_progress(self.brand_name, "extracting_products")
            
            email = os.getenv('KNOWDE_EMAIL')
            password = os.getenv('KNOWDE_PASSWORD')
            session = auth.get_auth_session(email, password)
            
            if not session:
                error_msg = "Ошибка получения сессии"
                processor.save_pipeline_progress(self.brand_name, "failed", error_msg)
                raise Exception(error_msg)
            
            try:
                service = BrandService(storage, processor, driver=session['driver'])
                logger.info(f"Извлечение продуктов для бренда: {self.brand_name}")
                products = service.extract_brand_products(self.brand_name)
                logger.info(f"Извлечено продуктов: {len(products)}")
                
                with self.output().open('w') as f:
                    f.write(json.dumps(products, indent=2))
                processor.save_pipeline_progress(self.brand_name, "completed")
                logger.info(f"Продукты бренда {self.brand_name} сохранены")
                
            finally:
                if session and 'driver' in session:
                    session['driver'].quit()
                    
        except Exception as e:
            error_msg = f"Ошибка при извлечении продуктов для бренда {self.brand_name}: {str(e)}"
            logger.error(error_msg)
            processor.save_pipeline_progress(self.brand_name, "failed", str(e))
            raise

class CollectBrandsTask(luigi.Task):
    """Задача для сбора списка брендов"""
    date = luigi.DateParameter(default=datetime.now())
    
    def output(self):
        output_path = str(PIPELINE_DIR / f"brands_collected_{self.date}.json")
        logger.info(f"Путь для сохранения брендов: {output_path}")
        return luigi.LocalTarget(output_path)
    
    def run(self):
        try:
            storage = BrandStorage()
            processor = BrandProcessor(storage)
            auth = KnowdeAuth()
            
            logger.info(f"Проверка директорий:")
            logger.info(f"PIPELINE_DIR exists: {PIPELINE_DIR.exists()}")
            logger.info(f"PIPELINE_DIR path: {PIPELINE_DIR}")
            
            processor.save_pipeline_progress("collect_brands", "processing")
            
            logger.info("Начало процесса аутентификации...")
            session = auth.get_auth_session(os.getenv('KNOWDE_EMAIL'), os.getenv('KNOWDE_PASSWORD'))
            
            if not session:
                error_msg = "Ошибка получения сессии"
                processor.save_pipeline_progress("collect_brands", "failed", error_msg)
                logger.error(error_msg)
                raise Exception(error_msg)
            
            try:
                parser = BrandParser(storage, session)
                logger.info("Начинаем сбор брендов...")
                parser.collect_brand_links()
                
                # Сохраняем список брендов в JSON
                brands_data = []
                for brand_url in parser.brand_links:
                    brand_name = brand_url.split('/')[-1]
                    brands_data.append({
                        "name": brand_name,
                        "url": brand_url
                    })
                
                logger.info(f"Собрано брендов: {len(brands_data)}")
                logger.info(f"Сохранение в файл: {self.output().path}")
                
                # Создаем директорию если её нет
                os.makedirs(os.path.dirname(self.output().path), exist_ok=True)
                
                with self.output().open('w') as f:
                    json.dump(brands_data, f, indent=2)
                
                processor.save_pipeline_progress("collect_brands", "completed")
                logger.info(f"Данные успешно сохранены в {self.output().path}")
                        
            finally:
                if session and 'driver' in session:
                    session['driver'].quit()
                    
        except Exception as e:
            error_msg = f"Ошибка при сборе списка брендов: {str(e)}"
            logger.error(error_msg)
            processor.save_pipeline_progress("collect_brands", "failed", str(e))
            raise

class KnowdePipeline(luigi.Task):
    """Основная задача пайплайна"""
    date = luigi.DateParameter(default=datetime.now())
    
    def requires(self):
        collect_task = CollectBrandsTask(date=self.date)
        
        if collect_task.output().exists():
            logger.info("Загрузка списка собранных брендов...")
            with collect_task.output().open('r') as f:
                brands_data = json.load(f)
            
            logger.info(f"Запуск обработки для {len(brands_data)} брендов")
            return {
                'collect': collect_task,
                'extract': [
                    ExtractProductsTask(
                        date=self.date,
                        brand_name=brand['name'],
                        brand_url=brand['url']
                    ) for brand in brands_data
                ]
            }
        else:
            logger.info("Запуск сбора брендов...")
            return {'collect': collect_task}
    
    def output(self):
        return luigi.LocalTarget(str(PIPELINE_DIR / f"pipeline_complete_{self.date}.mark"))
    
    def run(self):
        with self.output().open('w') as f:
            f.write(f'Pipeline completed successfully at {datetime.now()}')
        logger.info("Пайплайн успешно завершен!")

if __name__ == "__main__":
    logger.info("Запуск пайплайна...")
    luigi.build(
        [KnowdePipeline()], 
        local_scheduler=True, 
        workers=3,
        log_level='INFO'
    )

