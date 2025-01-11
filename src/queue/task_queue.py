"""Модуль для работы с очередями задач."""
import os
from typing import Optional, Dict, Any
from redis import Redis
from rq import Queue, Worker
from rq.job import Job

class TaskQueue:
    def __init__(self):
        self.redis = Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        self.brand_queue = Queue('brand_processing', connection=self.redis)
        self.product_queue = Queue('product_extraction', connection=self.redis)

    def enqueue_brand_processing(self, brand_name: str, priority: int = 1) -> Optional[Job]:
        """Добавление задачи на обработку бренда в очередь"""
        try:
            return self.brand_queue.enqueue(
                'src.tasks.process_brand',
                args=(brand_name,),
                job_timeout='1h',
                result_ttl=24*3600,  # Храним результат 24 часа
                priority=priority
            )
        except Exception as e:
            print(f"Ошибка при добавлении бренда {brand_name} в очередь: {e}")
            return None

    def enqueue_product_extraction(self, brand_name: str, priority: int = 1) -> Optional[Job]:
        """Добавление задачи на извлечение продуктов в очередь"""
        try:
            return self.product_queue.enqueue(
                'src.tasks.extract_products',
                args=(brand_name,),
                job_timeout='2h',
                result_ttl=24*3600,
                priority=priority
            )
        except Exception as e:
            print(f"Ошибка при добавлении извлечения продуктов для {brand_name} в очередь: {e}")
            return None

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Получение статуса задачи"""
        job = Job.fetch(job_id, connection=self.redis)
        return {
            'id': job.id,
            'status': job.get_status(),
            'result': job.result,
            'error': job.exc_info,
            'enqueued_at': job.enqueued_at,
            'started_at': job.started_at,
            'ended_at': job.ended_at
        }

    def clear_failed_jobs(self):
        """Очистка неудачных задач"""
        self.brand_queue.delete_failed_jobs()
        self.product_queue.delete_failed_jobs()

    def requeue_failed_jobs(self):
        """Перезапуск неудачных задач"""
        self.brand_queue.requeue_failed_jobs()
        self.product_queue.requeue_failed_jobs()

    def enqueue_brand_for_processing(self, brand_name: str) -> None:
        """Добавление бренда в очередь на обработку"""
        if not self.redis.sismember('processed_brands', brand_name):
            self.redis.rpush('brands_queue', brand_name)
            print(f"Бренд {brand_name} добавлен в очередь")

    def get_next_brand(self) -> Optional[str]:
        """Получение следующего бренда из очереди"""
        brand = self.redis.lpop('brands_queue')
        if brand:
            self.redis.sadd('processed_brands', brand)
            return brand.decode('utf-8')
        return None 