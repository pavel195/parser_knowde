"""
API endpoints для доступа к данным брендов.
Предоставляет endpoints для получения JSON-данных.

Примеры использования:
    Получение списка брендов:
    GET /brands/

    Получение данных бренда:
    GET /brands/accor
    GET /brands/accor?include_products=true

    Получение сводки:
    GET /brands/accor/summary

    Поиск продуктов:
    GET /brands/accor/products
    GET /brands/accor/products?category=Surfactants&keyword=natural
"""
from fastapi import FastAPI, HTTPException
from typing import List, Optional
import uvicorn

from src.service.brand_service import BrandService
from src.storage.brand_storage import BrandStorage
from src.processor.brand_processor import BrandProcessor

app = FastAPI(title="Knowde Brand Parser API")

# Инициализация сервисов
storage = BrandStorage()
processor = BrandProcessor(storage)
service = BrandService(storage, processor)

@app.get("/brands/", response_model=List[str])
async def get_brands():
    """Получение списка всех доступных брендов"""
    return service.list_available_brands()

@app.get("/brands/{brand_name}")
async def get_brand_data(brand_name: str, include_products: bool = False):
    """Получение данных о конкретном бренде"""
    data = service.get_brand_data(brand_name, include_products)
    if not data:
        raise HTTPException(status_code=404, detail="Brand not found")
    return data

@app.get("/brands/{brand_name}/summary")
async def get_brand_summary(brand_name: str):
    """Получение краткой сводки о бренде"""
    summary = service.get_brand_summary(brand_name)
    if not summary:
        raise HTTPException(status_code=404, detail="Brand not found")
    return summary

@app.get("/brands/{brand_name}/products")
async def get_brand_products(
    brand_name: str, 
    category: Optional[str] = None,
    keyword: Optional[str] = None
):
    """Поиск продуктов бренда"""
    products = service.search_products(brand_name, category, keyword)
    if products is None:
        raise HTTPException(status_code=404, detail="Brand not found")
    return products

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 