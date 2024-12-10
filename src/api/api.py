"""
API для доступа к данным брендов.
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

from brand_storage import BrandStorage
from brand_data_processor import BrandDataProcessor

app = FastAPI(title="Knowde Brand Parser API")
storage = BrandStorage()
processor = BrandDataProcessor(storage)

@app.get("/brands/", response_model=List[str])
async def get_brands():
    """Получение списка всех доступных брендов"""
    return storage.list_brands()

@app.get("/brands/{brand_name}")
async def get_brand_data(brand_name: str, include_products: bool = False):
    """
    Получение данных о конкретном бренде
    Args:
        brand_name: Название бренда
        include_products: Включать ли информацию о продуктах
    """
    data = storage.load_brand_data(brand_name)
    if not data:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    if not include_products:
        # Убираем детальную информацию о продуктах для уменьшения размера ответа
        data['pageProps'].pop('most_viewed_products', None)
    
    return data

@app.get("/brands/{brand_name}/summary")
async def get_brand_summary(brand_name: str):
    """Получение краткой сводки о бренде"""
    summary = processor.get_brand_summary(brand_name)
    if not summary:
        raise HTTPException(status_code=404, detail="Brand not found")
    return summary

@app.get("/brands/{brand_name}/products")
async def get_brand_products(
    brand_name: str, 
    category: Optional[str] = None,
    keyword: Optional[str] = None
):
    """
    Поиск продуктов бренда
    Args:
        brand_name: Название бренда
        category: Фильтр по категории
        keyword: Поиск по ключевому слову
    """
    products = processor.search_products(brand_name, category, keyword)
    if products is None:
        raise HTTPException(status_code=404, detail="Brand not found")
    return products

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 