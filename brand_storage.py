import os
import json
import csv
from typing import List, Dict, Optional, Set

class BrandStorage:
    def __init__(self, data_directory: str = "brand_data"):
        self.data_directory = data_directory
        if not os.path.exists(data_directory):
            os.makedirs(data_directory)

    def save_brand_data(self, brand_name: str, data: Dict) -> None:
        """Сохранение данных бренда"""
        file_path = os.path.join(self.data_directory, f"{brand_name}.json")
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    def load_brand_data(self, brand_name: str) -> Optional[Dict]:
        """Загрузка данных бренда"""
        try:
            file_path = os.path.join(self.data_directory, f"{brand_name}.json")
            if not os.path.exists(file_path):
                return None
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            print(f"Ошибка при загрузке данных бренда {brand_name}: {str(e)}")
            return None

    def save_brand_links(self, links: Set[str], filename: str = "unique_brand_links.csv") -> None:
        """Сохранение ссылок на бренды"""
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Brand URL"])
            for link in links:
                writer.writerow([link])

    def load_brand_links(self, filename: str = "unique_brand_links.csv") -> List[str]:
        """Загрузка ссылок на бренды"""
        links = []
        if not os.path.exists(filename):
            return links
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)
            links = [row[0] for row in reader if row]
        return links

    def list_brands(self) -> List[str]:
        """Получение списка доступных брендов"""
        try:
            files = os.listdir(self.data_directory)
            return [f.replace('.json', '') for f in files if f.endswith('.json')]
        except Exception as e:
            print(f"Ошибка при получении списка брендов: {str(e)}")
            return [] 