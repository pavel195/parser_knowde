#!/usr/bin/env python
import os
from src.auth.knowde_auth import KnowdeAuth
from src.storage.db_storage import DBStorage
from src.queue.task_queue import TaskQueue
from src.processor.product_extractor import ProductExtractor

def main():
    try:
        # Инициализация компонентов
        auth = KnowdeAuth()
        storage = DBStorage()
        queue = TaskQueue()
        
        print("Запуск обработчика продуктов...")
        
        # Получаем авторизованную сессию
        session = auth.get_auth_session(
            os.getenv('KNOWDE_EMAIL'),
            os.getenv('KNOWDE_PASSWORD')
        )
        
        if not session:
            raise Exception("Не удалось получить сессию")
            
        # Создаем экстрактор и запускаем обработку
        extractor = ProductExtractor(storage, session['driver'])
        extractor.run()  # Бесконечный цикл обработки
        
    except Exception as e:
        print(f"Ошибка в экстракторе продуктов: {e}")
        raise
    finally:
        if 'session' in locals() and session.get('driver'):
            session['driver'].quit()

if __name__ == "__main__":
    main() 