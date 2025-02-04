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


project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.parser.brand_parser import BrandParser
from src.storage.brand_storage import BrandStorage
from src.processor.brand_processor import BrandProcessor
from src.service.brand_service import BrandService
from src.auth.knowde_auth import KnowdeAuth

# Базовые пути проекта
DATA_DIR = project_root / "data"
BRAND_DATA_DIR = DATA_DIR / "brand_data"
PRODUCTS_DIR = DATA_DIR / "products"
PIPELINE_DIR = DATA_DIR / "pipeline"
LOGS_DIR = DATA_DIR / "logs"

# Создаем все необходимые директории
for directory in [DATA_DIR, BRAND_DATA_DIR, PRODUCTS_DIR, PIPELINE_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

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
            auth = KnowdeAuth()
            
            print(f"\nНачало сохранения бренда: {self.brand_name}")
            
            email = os.getenv('KNOWDE_EMAIL')
            password = os.getenv('KNOWDE_PASSWORD')
            session = auth.get_auth_session(email, password)
            
            if not session:
                raise Exception("Ошибка получения сессии")
            
            try:
                parser = BrandParser(storage, session)
                print(f"Парсинг бренда: {self.brand_name}")
                json_data = parser._get_json_data_for_brand(self.brand_url)
                if json_data:
                    storage.save_brand_data(self.brand_name, json_data)
                    print(f"Бренд {self.brand_name} успешно сохранен")
                else:
                    raise Exception(f"Не удалось получить данные для бренда {self.brand_name}")
                
            finally:
                if session and 'driver' in session:
                    session['driver'].quit()
                    
        except Exception as e:
            print(f"Ошибка при сохранении бренда {self.brand_name}: {str(e)}")
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
            auth = KnowdeAuth()
            
            print(f"\nНачало извлечения продуктов для бренда: {self.brand_name}")
            
            email = os.getenv('KNOWDE_EMAIL')
            password = os.getenv('KNOWDE_PASSWORD')
            session = auth.get_auth_session(email, password)
            
            if not session:
                raise Exception("Ошибка получения сессии")
            
            try:
                processor = BrandProcessor(storage)
                service = BrandService(storage, processor, driver=session['driver'])
                print(f"Извлечение продуктов для бренда: {self.brand_name}")
                products = service.extract_brand_products(self.brand_name)
                print(f"Извлечено продуктов: {len(products)}")
                
                
                with self.output().open('w') as f:
                    f.write(json.dumps(products, indent=2))
                print(f"Продукты бренда {self.brand_name} сохранены\n")
                
            finally:
                if session and 'driver' in session:
                    session['driver'].quit()
                    
        except Exception as e:
            print(f"Ошибка при извлечении продуктов для бренда {self.brand_name}: {str(e)}")
            raise

class CollectBrandsTask(luigi.Task):
    """Задача для сбора списка брендов"""
    date = luigi.DateParameter(default=datetime.now())
    
    def output(self):
        return luigi.LocalTarget(str(PIPELINE_DIR / f"brands_collected_{self.date}.json"))
    
    def run(self):
        try:
            storage = BrandStorage()
            auth = KnowdeAuth()
            session = auth.get_auth_session(os.getenv('KNOWDE_EMAIL'), os.getenv('KNOWDE_PASSWORD'))
            
            if not session:
                raise Exception("Ошибка получения сессии")
            
            try:
                parser = BrandParser(storage, session)
                print("\nНачинаем сбор брендов...")
                parser.collect_brand_links()
                
                # Сохраняем список брендов в JSON
                brands_data = []
                for brand_url in parser.brand_links:
                    brand_name = brand_url.split('/')[-1]
                    brands_data.append({
                        "name": brand_name,
                        "url": brand_url
                    })
                
                with self.output().open('w') as f:
                    json.dump(brands_data, f, indent=2)
                print(f"Собрано брендов: {len(brands_data)}\n")
                        
            finally:
                if session and 'driver' in session:
                    session['driver'].quit()
                    
        except Exception as e:
            print(f"Ошибка при сборе списка брендов: {str(e)}")
            raise

class KnowdePipeline(luigi.Task):
    """Основная задача пайплайна"""
    date = luigi.DateParameter(default=datetime.now())
    
    def requires(self):
        """
        Определяет зависимости для пайплайна:
        1. Сначала собираем бренды
        2. Затем для каждого бренда запускаем извлечение продуктов
        """
        
        collect_task = CollectBrandsTask(date=self.date)
        
        
        if collect_task.output().exists():
            
            with collect_task.output().open('r') as f:
                brands_data = json.load(f)
            
            
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
            
            return {'collect': collect_task}
    
    def output(self):
        return luigi.LocalTarget(str(PIPELINE_DIR / f"pipeline_complete_{self.date}.mark"))
    
    def run(self):
        with self.output().open('w') as f:
            f.write(f'Pipeline completed successfully at {datetime.now()}')
        print("\nПайплайн успешно завершен!")

if __name__ == "__main__":
    print("\nЗапуск пайплайна...")
    luigi.build(
        [KnowdePipeline()], 
        local_scheduler=True, 
        workers=3,
        log_level='INFO'
    )

