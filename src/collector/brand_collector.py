def process_brands(self):
    """Обработка брендов"""
    brands = self.get_brands()
    for brand in brands:
        # Сохраняем бренд
        self.storage.save_brand_data(brand_name, brand_data)
        # Добавляем в очередь на извлечение продуктов
        self.queue.enqueue_brand_for_processing(brand_name) 