"""Модуль для работы с хранением данных."""
import os
import json
from typing import Dict, List, Optional, Set
from pathlib import Path

class BrandStorage:
    def __init__(self, data_dir: str = "data/brand_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def save_brand_data(self, brand_name: str, data: Dict) -> None:
        """Сохранение данных бренда"""
        file_path = self.data_dir / f"{brand_name}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_brand_data(self, brand_name: str) -> Optional[Dict]:
        """Загрузка данных бренда"""
        file_path = self.data_dir / f"{brand_name}.json"
        try:
            if not file_path.exists():
                return None
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка при загрузке {brand_name}: {e}")
            return None

    def list_brands(self) -> List[str]:
        """Получение списка брендов"""
        return [f.stem for f in self.data_dir.glob("*.json")] 