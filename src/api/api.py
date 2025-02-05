"""API для доступа к данным парсера Knowde."""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict
import uvicorn
import json
from pathlib import Path

from src.service.brand_service import BrandService
from src.storage.brand_storage import BrandStorage
from src.processor.brand_processor import BrandProcessor

app = FastAPI(
    title="Knowde Brand Parser API",
    description="API для доступа к данным о брендах и продуктах с Knowde",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация сервисов
storage = BrandStorage()
processor = BrandProcessor(storage)
service = BrandService(storage, processor)

@app.get("/", tags=["Общее"])
async def root():
    """Проверка работоспособности API."""
    return {"status": "ok", "message": "Knowde Parser API работает"}

@app.get("/brands/", response_model=List[str], tags=["Бренды"])
async def get_brands():
    """
    Получение списка всех доступных брендов.
    
    Returns:
        List[str]: Список названий брендов
    """
    try:
        brands = service.list_available_brands()
        if not brands:
            return []
        return brands
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/brands/{brand_name}", tags=["Бренды"])
async def get_brand_data(
    brand_name: str,
    include_products: bool = Query(False, description="Включить данные о продуктах")
):
    """
    Получение данных о конкретном бренде.
    
    Args:
        brand_name: Название бренда
        include_products: Включать ли информацию о продуктах
        
    Returns:
        Dict: Данные о бренде
    """
    try:
        data = service.get_brand_data(brand_name, include_products)
        if not data:
            raise HTTPException(status_code=404, detail=f"Бренд {brand_name} не найден")
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/brands/{brand_name}/summary", tags=["Бренды"])
async def get_brand_summary(brand_name: str):
    """
    Получение краткой сводки о бренде.
    
    Args:
        brand_name: Название бренда
        
    Returns:
        Dict: Краткая информация о бренде
    """
    try:
        summary = service.get_brand_summary(brand_name)
        if not summary:
            raise HTTPException(status_code=404, detail=f"Бренд {brand_name} не найден")
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/brands/{brand_name}/products", tags=["Продукты"])
async def get_brand_products(
    brand_name: str,
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    keyword: Optional[str] = Query(None, description="Поиск по ключевому слову")
):
    """
    Поиск продуктов бренда.
    
    Args:
        brand_name: Название бренда
        category: Категория продуктов (опционально)
        keyword: Ключевое слово для поиска (опционально)
        
    Returns:
        List[Dict]: Список продуктов
    """
    try:
        products = service.search_products(brand_name, category, keyword)
        if products is None:
            raise HTTPException(status_code=404, detail=f"Бренд {brand_name} не найден")
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products/search", tags=["Продукты"])
async def search_all_products(
    keyword: str = Query(..., description="Ключевое слово для поиска"),
    category: Optional[str] = Query(None, description="Фильтр по категории")
):
    """
    Поиск по всем продуктам во всех брендах.
    
    Args:
        keyword: Ключевое слово для поиска
        category: Категория продуктов (опционально)
        
    Returns:
        List[Dict]: Список найденных продуктов
    """
    try:
        results = []
        brands = service.list_available_brands()
        
        for brand in brands:
            products = service.search_products(brand, category, keyword)
            if products:
                results.extend(products)
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pipeline/status", tags=["Пайплайн"])
async def get_pipeline_status():
    """
    Получение текущего статуса выполнения пайплайна.
    
    Returns:
        Dict: Статистика обработки брендов
    """
    try:
        status = processor.get_pipeline_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pipeline/reset", tags=["Пайплайн"])
async def reset_pipeline_progress():
    """
    Сброс прогресса выполнения пайплайна.
    
    Returns:
        Dict: Результат операции
    """
    try:
        success = processor.clear_pipeline_progress()
        if success:
            return {"status": "success", "message": "Прогресс пайплайна успешно сброшен"}
        else:
            raise HTTPException(status_code=500, detail="Не удалось сбросить прогресс пайплайна")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pipeline/failed-brands", tags=["Пайплайн"])
async def get_failed_brands():
    """
    Получение списка брендов, при обработке которых произошли ошибки.
    
    Returns:
        List[Dict]: Список брендов с ошибками
    """
    try:
        status = processor.get_pipeline_status()
        failed_brands = [
            {
                'name': name,
                'error': info['error'],
                'timestamp': info['timestamp']
            }
            for name, info in status['brands'].items()
            if info['status'] == 'failed'
        ]
        return failed_brands
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 