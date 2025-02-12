"""Модуль для хранения данных о брендах."""
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy import and_

from src.database.db import get_db
from src.database.models import Brand, Product

class BrandStorage:
    def save_brand_data(self, brand_name: str, data: Dict) -> None:
        """
        Сохранение данных бренда.
        
        Args:
            brand_name: Название бренда
            data: Данные бренда в формате JSON
        """
        try:
            with get_db() as db:
                brand = db.query(Brand).filter(Brand.name == brand_name).first()
                
                if not brand:
                    brand = Brand(name=brand_name)
                    db.add(brand)
                
                brand.data = data
                brand.updated_at = datetime.utcnow()
                
                # Извлекаем дополнительные данные из JSON
                if 'pageProps' in data:
                    props = data['pageProps']
                    if 'url' in props:
                        brand.url = props['url']
                    if 'category' in props:
                        brand.category = props['category']
                
                db.commit()
                
        except Exception as e:
            print(f"Ошибка при сохранении данных бренда {brand_name}: {str(e)}")

    def load_brand_data(self, brand_name: str) -> Optional[Dict]:
        """
        Загрузка данных бренда.
        
        Args:
            brand_name: Название бренда
            
        Returns:
            Dict: Данные бренда или None, если бренд не найден
        """
        try:
            with get_db() as db:
                brand = db.query(Brand).filter(Brand.name == brand_name).first()
                return brand.data if brand else None
                
        except Exception as e:
            print(f"Ошибка при загрузке данных бренда {brand_name}: {str(e)}")
            return None

    def list_brands(self) -> List[str]:
        """
        Получение списка всех брендов.
        
        Returns:
            List[str]: Список названий брендов
        """
        try:
            with get_db() as db:
                brands = db.query(Brand.name).all()
                return [brand[0] for brand in brands]
                
        except Exception as e:
            print(f"Ошибка при получении списка брендов: {str(e)}")
            return []

    def save_product(self, brand_name: str, product_id: str, data: Dict) -> None:
        """
        Сохранение данных продукта.
        
        Args:
            brand_name: Название бренда
            product_id: ID продукта
            data: Данные продукта в формате JSON
        """
        try:
            with get_db() as db:
                # Получаем бренд
                brand = db.query(Brand).filter(Brand.name == brand_name).first()
                if not brand:
                    print(f"Бренд {brand_name} не найден")
                    return
                
                # Получаем или создаем продукт
                product = db.query(Product).filter(
                    and_(
                        Product.brand_id == brand.id,
                        Product.product_id == product_id
                    )
                ).first()
                
                if not product:
                    product = Product(
                        product_id=product_id,
                        brand_id=brand.id
                    )
                    db.add(product)
                
                # Обновляем данные продукта
                product.data = data
                product.name = data.get('name')
                product.url = data.get('url')
                product.description = data.get('description')
                product.updated_at = datetime.utcnow()
                
                db.commit()
                
        except Exception as e:
            print(f"Ошибка при сохранении продукта {product_id}: {str(e)}")

    def load_product(self, brand_name: str, product_id: str) -> Optional[Dict]:
        """
        Загрузка данных продукта.
        
        Args:
            brand_name: Название бренда
            product_id: ID продукта
            
        Returns:
            Dict: Данные продукта или None, если продукт не найден
        """
        try:
            with get_db() as db:
                product = db.query(Product).join(Brand).filter(
                    and_(
                        Brand.name == brand_name,
                        Product.product_id == product_id
                    )
                ).first()
                
                return product.data if product else None
                
        except Exception as e:
            print(f"Ошибка при загрузке продукта {product_id}: {str(e)}")
            return None 