from brand_storage import BrandStorage
from brand_data_processor import BrandDataProcessor
from brand_service import BrandService
from combined_brands_parser import BrandParser

def main():
    # Инициализация компонентов
    storage = BrandStorage()
    processor = BrandDataProcessor(storage)
    service = BrandService(storage, processor)
    parser = BrandParser(storage)

    # Сбор данных
    parser.run_full_process()

    # Анализ данных
    brands = service.list_available_brands()
    for brand_name in brands:
        summary = service.get_brand_summary(brand_name)
        if summary:
            print(f"\nАнализ бренда: {brand_name}")
            print(json.dumps(summary, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main() 