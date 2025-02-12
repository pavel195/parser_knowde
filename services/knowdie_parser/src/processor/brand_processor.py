"""Модуль для обработки данных брендов."""
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.storage.brand_storage import BrandStorage
from src.database.db import get_db
from src.database.models import Brand, Product, PipelineProgress, ProcessStatus

class BrandProcessor:
    def __init__(self, storage: BrandStorage):
        self.storage = storage

    def save_pipeline_progress(self, brand_name: str, status: str = "completed", 
                             error: Optional[str] = None, **kwargs) -> None:
        """
        Сохранение прогресса обработки бренда.
        
        Args:
            brand_name: Название бренда
            status: Статус обработки (completed/failed/processing)
            error: Описание ошибки, если есть
            **kwargs: Дополнительные параметры (category, url и т.д.)
        """
        try:
            with get_db() as db:
                # Получаем или создаем бренд
                brand = self._get_or_create_brand(db, brand_name, **kwargs)
                
                # Получаем или создаем запись о прогрессе
                progress = db.query(PipelineProgress).filter(
                    PipelineProgress.brand_id == brand.id
                ).first()
                
                if not progress:
                    progress = PipelineProgress(brand_id=brand.id)
                    db.add(progress)
                
                # Обновляем статус
                progress.status = ProcessStatus[status.upper()]
                progress.error = error
                progress.updated_at = datetime.utcnow()
                
                db.commit()
                
        except Exception as e:
            print(f"Ошибка при сохранении прогресса для бренда {brand_name}: {str(e)}")

    def get_pipeline_status(self) -> Dict[str, Any]:
        """
        Получение статуса выполнения пайплайна.
        
        Returns:
            Dict: Статистика обработки брендов
        """
        try:
            with get_db() as db:
                # Получаем все записи о прогрессе
                progress_records = db.query(PipelineProgress).join(Brand).all()
                
                # Считаем статистику
                total = len(progress_records)
                completed = sum(1 for p in progress_records if p.status == ProcessStatus.COMPLETED)
                failed = sum(1 for p in progress_records if p.status == ProcessStatus.FAILED)
                
                # Находим время последнего обновления
                last_update = max(
                    (p.updated_at for p in progress_records),
                    default=None
                )
                
                # Формируем детальную информацию по брендам
                brands = {}
                for progress in progress_records:
                    brands[progress.brand.name] = {
                        'status': progress.status.value,
                        'timestamp': progress.updated_at.isoformat() if progress.updated_at else None,
                        'error': progress.error,
                        'category': progress.brand.category,
                        'url': progress.brand.url
                    }
                
                return {
                    'total': total,
                    'completed': completed,
                    'failed': failed,
                    'last_update': last_update.isoformat() if last_update else None,
                    'brands': brands
                }
                
        except Exception as e:
            print(f"Ошибка при получении статуса пайплайна: {str(e)}")
            return {
                'total': 0,
                'completed': 0,
                'failed': 0,
                'last_update': None,
                'brands': {}
            }

    def get_unprocessed_brands(self) -> List[Dict[str, str]]:
        """
        Получение списка необработанных брендов.
        
        Returns:
            List[Dict[str, str]]: Список брендов для обработки
        """
        try:
            with get_db() as db:
                # Получаем бренды без прогресса или с ошибками
                unprocessed = db.query(Brand).outerjoin(
                    PipelineProgress
                ).filter(
                    and_(
                        PipelineProgress.id.is_(None) |
                        (PipelineProgress.status == ProcessStatus.FAILED)
                    )
                ).all()
                
                return [
                    {'name': brand.name, 'url': brand.url}
                    for brand in unprocessed
                ]
                
        except Exception as e:
            print(f"Ошибка при получении списка необработанных брендов: {str(e)}")
            return []

    def clear_pipeline_progress(self) -> bool:
        """
        Очистка прогресса пайплайна.
        
        Returns:
            bool: True если очистка успешна, False в случае ошибки
        """
        try:
            with get_db() as db:
                db.query(PipelineProgress).delete()
                db.commit()
                return True
        except Exception as e:
            print(f"Ошибка при очистке прогресса пайплайна: {str(e)}")
            return False

    def _get_or_create_brand(self, db: Session, brand_name: str, **kwargs) -> Brand:
        """
        Получение или создание записи о бренде.
        
        Args:
            db: Сессия базы данных
            brand_name: Название бренда
            **kwargs: Дополнительные параметры бренда
            
        Returns:
            Brand: Объект бренда
        """
        brand = db.query(Brand).filter(Brand.name == brand_name).first()
        
        if not brand:
            brand = Brand(
                name=brand_name,
                url=kwargs.get('url', ''),
                category=kwargs.get('category')
            )
            db.add(brand)
            db.flush()
        
        return brand

        data = self.storage.load_brand_data(brand_name)
        if not data:
            return None
            
        company_info = data.get('pageProps', {})
        products = company_info.get('most_viewed_products', {}).get('data', [])
        
        return {
            'name': company_info.get('name'),
            'description': company_info.get('description'),
            'total_products': len(products),
            'categories': self._get_unique_categories(products),
            'website': company_info.get('social_links', [{}])[0].get('url'),
            'location': company_info.get('hq_address')
        }
        
    def _get_unique_categories(self, products: List[Dict]) -> List[str]:
        """
        Получение уникальных категорий из списка продуктов.
        
        Args:
            products: Список продуктов
            
        Returns:
            List[str]: Список уникальных категорий
        """
        categories = set()
        for product in products:
            if 'categories' in product:
                categories.update(product['categories'])
        return sorted(list(categories))

    def search_products(self, brand_name: str, category: Optional[str] = None, 
                       keyword: Optional[str] = None) -> List[Dict]:
        """
        Поиск продуктов бренда с фильтрацией.
        
        Args:
            brand_name: Название бренда
            category: Категория для фильтрации
            keyword: Ключевое слово для поиска
            
        Returns:
            List[Dict]: Список найденных продуктов
        """
        try:
            brand_products_dir = self.products_dir / brand_name
            if not brand_products_dir.exists():
                return []

            results = []
            
            # Читаем все файлы продуктов бренда
            for product_file in brand_products_dir.glob("*.json"):
                try:
                    with open(product_file, 'r', encoding='utf-8') as f:
                        product = json.load(f)
                    
                    # Проверяем категорию
                    if category:
                        product_categories = product.get('categories', [])
                        if not product_categories or category not in product_categories:
                            continue
                    
                    # Проверяем ключевое слово
                    if keyword:
                        keyword = keyword.lower()
                        searchable_fields = [
                            product.get('name', ''),
                            product.get('description', ''),
                            product.get('summary', ''),
                            *[str(v) for v in product.get('properties', {}).values()],
                            *product.get('categories', [])
                        ]
                        
                        searchable_text = ' '.join(str(field).lower() for field in searchable_fields)
                        if keyword not in searchable_text:
                            continue
                    
                    results.append(product)
                    
                except Exception as e:
                    print(f"Ошибка при обработке файла {product_file}: {str(e)}")
                    continue
            
            return results
            
        except Exception as e:
            print(f"Ошибка при поиске продуктов бренда {brand_name}: {str(e)}")
            return []

    def get_product_details(self, brand_name: str, product_id: str) -> Optional[Dict]:
        """
        Получение детальной информации о продукте.
        
        Args:
            brand_name: Название бренда
            product_id: ID продукта
            
        Returns:
            Dict: Данные о продукте или None, если продукт не найден
        """
        try:
            product_file = self.products_dir / brand_name / f"{product_id}.json"
            if not product_file.exists():
                return None
                
            with open(product_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            print(f"Ошибка при получении данных продукта {product_id}: {str(e)}")
            return None

    def get_brand_categories(self, brand_name: str) -> List[str]:
        """
        Получение списка всех категорий бренда.
        
        Args:
            brand_name: Название бренда
            
        Returns:
            List[str]: Список категорий
        """
        try:
            categories = set()
            brand_products_dir = self.products_dir / brand_name
            
            if not brand_products_dir.exists():
                return []
                
            for product_file in brand_products_dir.glob("*.json"):
                try:
                    with open(product_file, 'r', encoding='utf-8') as f:
                        product = json.load(f)
                        categories.update(product.get('categories', []))
                except Exception:
                    continue
                    
            return sorted(list(categories))
            
        except Exception as e:
            print(f"Ошибка при получении категорий бренда {brand_name}: {str(e)}")
            return []

