#!/usr/bin/env python
from src.auth.knowde_auth import KnowdeAuth
from src.storage.db_storage import DBStorage
from src.queue.task_queue import TaskQueue
from src.collector.brand_collector import BrandCollector
import os
def main():
    try:
        # Инициализация компонентов
        auth = KnowdeAuth()
        storage = DBStorage()
        queue = TaskQueue()
        
        print("Начинаем сбор и обработку брендов...")
        
        # Получаем авторизованную сессию
        session = auth.get_auth_session(
            os.getenv('KNOWDE_EMAIL'),
            os.getenv('KNOWDE_PASSWORD')
        )
        
        if not session:
            raise Exception("Не удалось получить сессию")
            
        # Создаем коллектор и запускаем обработку
        collector = BrandCollector(storage, queue, session['driver'])
        collector.process_brands()
        
    except Exception as e:
        print(f"Ошибка в коллекторе брендов: {e}")
        raise
    finally:
        if 'session' in locals() and session.get('driver'):
            session['driver'].quit()

if __name__ == "__main__":
    main() 