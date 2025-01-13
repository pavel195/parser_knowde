"""Модуль для работы с базой данных PostgreSQL."""
import os
import json
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extras import Json
import time

class DBStorage:
    def __init__(self):
        self.conn = None
        self.cur = None
        self.connect()
        self.create_tables()

    def connect(self):
        """Подключение к базе данных"""
        max_retries = 5
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                self.conn = psycopg2.connect(
                    os.getenv('DATABASE_URL'),
                    connect_timeout=10
                )
                self.cur = self.conn.cursor()
                
                # Проверяем подключение
                self.cur.execute('SELECT 1')
                print("Успешное подключение к базе данных")
                return
                
            except Exception as e:
                print(f"Попытка {attempt + 1}/{max_retries}: Ошибка подключения к базе данных: {e}")
                if self.conn:
                    self.conn.close()
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise

    def create_tables(self):
        """Создание необходимых таблиц"""
        try:
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS brands (
                    brand_name VARCHAR(255) PRIMARY KEY,
                    data JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS products (
                    id VARCHAR(255) PRIMARY KEY,
                    brand_name VARCHAR(255) REFERENCES brands(brand_name),
                    data JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            self.conn.commit()
        except Exception as e:
            print(f"Ошибка создания таблиц: {e}")
            self.conn.rollback()
            raise

    def save_brand_data(self, brand_name: str, data: Dict) -> None:
        """Сохранение данных бренда"""
        try:
            self.cur.execute("""
                INSERT INTO brands (brand_name, data)
                VALUES (%s, %s)
                ON CONFLICT (brand_name) 
                DO UPDATE SET data = EXCLUDED.data;
            """, (brand_name, Json(data)))
            self.conn.commit()
        except Exception as e:
            print(f"Ошибка сохранения бренда {brand_name}: {e}")
            self.conn.rollback()

    def load_brand_data(self, brand_name: str) -> Optional[Dict]:
        """Загрузка данных бренда"""
        try:
            self.cur.execute("""
                SELECT data FROM brands WHERE brand_name = %s;
            """, (brand_name,))
            result = self.cur.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Ошибка загрузки бренда {brand_name}: {e}")
            return None

    def list_brands(self) -> List[str]:
        """Получение списка брендов"""
        try:
            self.cur.execute("SELECT brand_name FROM brands;")
            return [row[0] for row in self.cur.fetchall()]
        except Exception as e:
            print(f"Ошибка получения списка брендов: {e}")
            return []

    def save_product(self, product: Dict) -> None:
        """Сохранение данных продукта"""
        try:
            self.cur.execute("""
                INSERT INTO products (id, brand_name, data)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) 
                DO UPDATE SET data = EXCLUDED.data;
            """, (product['id'], product['brand'], Json(product)))
            self.conn.commit()
        except Exception as e:
            print(f"Ошибка сохранения продукта {product.get('id')}: {e}")
            self.conn.rollback()

    def update_brand_status(self, brand_name: str, status: str, error: str = None) -> None:
        """Обновление статуса бренда"""
        try:
            self.cur.execute("""
                UPDATE brands 
                SET status = %s, 
                    error_message = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE brand_name = %s;
            """, (status, error, brand_name))
            self.conn.commit()
        except Exception as e:
            print(f"Ошибка обновления статуса бренда {brand_name}: {e}")
            self.conn.rollback()

    def update_extraction_status(self, brand_name: str, status: str, 
                               products_count: int = None, error: str = None) -> None:
        """Обновление статуса извлечения продуктов"""
        try:
            self.cur.execute("""
                UPDATE brands 
                SET products_extracted = %s,
                    products_count = COALESCE(%s, products_count),
                    last_processed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP,
                    error_message = %s
                WHERE brand_name = %s;
            """, (status == 'completed', products_count, error, brand_name))
            self.conn.commit()
        except Exception as e:
            print(f"Ошибка обновления статуса извлечения для {brand_name}: {e}")
            self.conn.rollback()

    def is_brand_products_extracted(self, brand_name: str) -> bool:
        """Проверка, извлечены ли продукты для бренда"""
        try:
            self.cur.execute("""
                SELECT products_extracted 
                FROM brands 
                WHERE brand_name = %s;
            """, (brand_name,))
            result = self.cur.fetchone()
            return result[0] if result else False
        except Exception as e:
            print(f"Ошибка проверки статуса извлечения для {brand_name}: {e}")
            return False

    def __del__(self):
        """Закрытие соединения при удалении объекта"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close() 