import time
import psycopg2
import os
from typing import Optional

def wait_for_postgres(max_retries: int = 30, delay: int = 2) -> Optional[bool]:
    """Ожидание готовности PostgreSQL"""
    url = os.getenv('DATABASE_URL')
    
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(url)
            cur = conn.cursor()
            cur.execute('SELECT 1')
            cur.close()
            conn.close()
            print("База данных готова к работе")
            return True
        except Exception as e:
            print(f"Попытка {attempt + 1}/{max_retries}: {str(e)}")
            time.sleep(delay)
    
    return None

if __name__ == "__main__":
    if not wait_for_postgres():
        print("Не удалось дождаться готовности базы данных")
        exit(1) 