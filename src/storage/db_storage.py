"""Модуль для работы с базой данных PostgreSQL."""
import os
import json
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extras import Json

class DBStorage:
    def __init__(self):
        self.conn = None
        self.cur = None
        self.connect()
        self.create_tables()

    def connect(self):
        """Подключение к базе данных"""
        try:
            self.conn = psycopg2.connect(os.getenv('DATABASE_URL'))
            self.cur = self.conn.cursor()
        except Exception as e:
            print(f"Ошибка подключения к базе данных: {e}")
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

    def __del__(self):
        """Закрытие соединения при удалении объекта"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close() 