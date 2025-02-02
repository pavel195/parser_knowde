"""Интерфейс для перевода через Kluster.ai API"""
import os
import json
import time
import logging
from typing import Dict, Any
from openai import OpenAI
from httpx import HTTPStatusError, TimeoutException
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

load_dotenv()

class TextTranslator:
    def __init__(self):
        api_key = os.getenv("KLUSTER_API_KEY")
        if not api_key:
            logging.error("KLUSTER_API_KEY не найден в переменных окружения")
            raise ValueError("KLUSTER_API_KEY не найден в переменных окружения")
            
        # Инициализация клиента с увеличенными таймаутами
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.kluster.ai/v1",
            timeout=180.0,  
            max_retries=3,  
        )
        
        # Настройки
        self.model = "deepseek-ai/DeepSeek-R1"
        self.max_retries = int(os.getenv("OPENAI_MAX_RETRIES", "5"))
        self.retry_delay = int(os.getenv("OPENAI_RETRY_DELAY", "60"))
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "5000"))
        self.max_wait_time = int(os.getenv("OPENAI_MAX_WAIT_TIME", "180"))  # Увеличиваем до 3 минут
        
        logging.info(f"Инициализация с моделью {self.model}")

        # Промпт для перевода
        self.system_message = (
            "Можешь ли перевести значения на русский в файле без потери контекста химической тематики: "
            "перевести нужно будет только values, ключи пусть останутся на английском их не трогай. "
        )

    def _handle_rate_limit(self, response_headers: Dict) -> None:
        """Обработка превышения лимита запросов"""
        reset_time = int(response_headers.get('x-ratelimit-reset', 60))
        retry_after = int(response_headers.get('retry-after', 60))
        limit = int(response_headers.get('x-ratelimit-limit', 1))
        remaining = int(response_headers.get('x-ratelimit-remaining', 0))
        wait_time = max(reset_time, retry_after)
        
        logging.debug(f"Rate Limit Info:")
        logging.debug(f"  - Limit: {limit} requests")
        logging.debug(f"  - Remaining: {remaining} requests")
        logging.debug(f"  - Reset Time: {reset_time} seconds")
        logging.debug(f"  - Retry After: {retry_after} seconds")
        logging.debug(f"  - Selected Wait Time: {wait_time} seconds")
        
        logging.info(f"Достигнут лимит запросов. Ожидание {wait_time} секунд до сброса лимита...")
        time.sleep(wait_time + 1) 

    def _handle_api_error(self, e: Exception, attempt: int, response_headers: Dict = None) -> None:
        """Обработка ошибок API с логированием"""
        if isinstance(e, HTTPStatusError):
            status_code = e.response.status_code
            logging.debug(f"Получен статус код: {status_code}")
            
            if status_code == 524:  
                wait_time = min(self.retry_delay * (2 ** attempt), self.max_wait_time)
                logging.warning(f"Таймаут Cloudflare (попытка {attempt + 1}/{self.max_retries})")
                logging.info(f"Ожидание {wait_time} секунд перед повторной попыткой...")
                time.sleep(wait_time)
            elif status_code == 429:  
                if response_headers:
                    self._handle_rate_limit(response_headers)
                else:
                    wait_time = min(self.retry_delay * (2 ** attempt), self.max_wait_time)
                    logging.info(f"Rate limit без заголовков, ожидание {wait_time} секунд...")
                    time.sleep(wait_time)
            else:
                wait_time = min(self.retry_delay * (2 ** attempt), self.max_wait_time)
                logging.warning(f"Ошибка HTTP {status_code} (попытка {attempt + 1}/{self.max_retries})")
                logging.info(f"Ожидание {wait_time} секунд...")
                time.sleep(wait_time)
        elif isinstance(e, TimeoutException):
            wait_time = min(self.retry_delay * (2 ** attempt), self.max_wait_time)
            logging.warning(f"Таймаут соединения (попытка {attempt + 1}/{self.max_retries})")
            logging.info(f"Ожидание {wait_time} секунд...")
            time.sleep(wait_time)
        else:
            wait_time = min(self.retry_delay * (2 ** attempt), self.max_wait_time)
            logging.warning(f"Неожиданная ошибка: {str(e)} (попытка {attempt + 1}/{self.max_retries})")
            logging.info(f"Ожидание {wait_time} секунд...")
            time.sleep(wait_time)

    def _chunk_json(self, data: Dict) -> list:
        """Разбивает большой JSON на части, если он превышает лимит токенов"""
        
        MAX_CHUNK_SIZE = 1000
        
        data_str = json.dumps(data, ensure_ascii=False)
        estimated_tokens = len(data_str) * 1.5
        logging.info(f"Размер входных данных: {len(data_str)} символов, примерно {estimated_tokens} токенов")

        if estimated_tokens > MAX_CHUNK_SIZE:
            result = []
            temp_dict = {}
            current_size = 0
            
            for key, value in data.items():
                value_str = json.dumps({key: value}, ensure_ascii=False)
                value_tokens = len(value_str) * 1.5
                
                if value_tokens > MAX_CHUNK_SIZE and isinstance(value, str):
                    parts = []
                    text = value
                    while text:
                        safe_length = int(MAX_CHUNK_SIZE / 1.5 / 2)
                        part = text[:safe_length]
                        text = text[safe_length:]
                        parts.append(part)
                    
                    for i, part in enumerate(parts):
                        part_dict = {f"{key}_part_{i+1}": part}
                        result.append(part_dict)
                    continue
                
                if current_size + value_tokens > MAX_CHUNK_SIZE:
                    if temp_dict:
                        result.append(temp_dict)
                        temp_dict = {}
                        current_size = 0
                
                temp_dict[key] = value
                current_size += value_tokens
                
                if current_size >= MAX_CHUNK_SIZE:
                    result.append(temp_dict)
                    temp_dict = {}
                    current_size = 0
            
            if temp_dict:
                result.append(temp_dict)
            
            logging.info(f"Данные разбиты на {len(result)} частей")
            return result
        return [data]

    def translate(self, data: Any) -> Any:
        """
        Универсальный метод перевода данных через Kluster.ai API
        
        Args:
            data: Данные для перевода (любого типа)
        Returns:
            Any: Переведенные данные того же типа
        """
        if not data:
            return data

        try:
            chunks = self._chunk_json(data)
            translated_chunks = []
            
            logging.debug(f"Подготовка к переводу:")
            logging.debug(f"  - Всего чанков: {len(chunks)}")
            for i, chunk in enumerate(chunks, 1):
                chunk_size = len(json.dumps(chunk, ensure_ascii=False))
                logging.debug(f"  - Чанк {i}: {chunk_size} символов")

            for i, chunk in enumerate(chunks, 1):
                chunk_translated = False
                data_json = json.dumps(chunk, ensure_ascii=False)
                logging.debug(f"\nНачало обработки чанка {i}/{len(chunks)}:")
                logging.debug(f"  - Размер JSON: {len(data_json)} символов")
                logging.debug(f"  - Содержимое: {data_json[:200]}...")

                for attempt in range(self.max_retries):
                    try:
                        logging.debug(f"\nПопытка {attempt + 1}/{self.max_retries} для чанка {i}:")
                        start_time = time.time()
                        response = self.client.chat.completions.create(
                            model=self.model,
                            messages=[
                                {"role": "system", "content": self.system_message},
                                {"role": "user", "content": data_json}
                            ],
                            max_completion_tokens=1000,
                            temperature=0.6,
                            top_p=1
                        )
                        elapsed_time = time.time() - start_time
                        logging.debug(f"Время выполнения запроса: {elapsed_time:.2f} секунд")

                        translated_json = response.choices[0].message.content.strip()
                        logging.debug(f"  - Получен ответ: {translated_json[:200]}...")
                        
                        try:
                            translated_chunk = json.loads(translated_json)
                            logging.debug("  - JSON успешно распарсен")
                        except json.JSONDecodeError as je:
                            logging.warning(f"Ошибка парсинга JSON: {str(je)}")
                            logging.debug(f"Попытка очистки ответа API: {translated_json[:200]}...")
                            translated_json = translated_json.strip('`').strip()
                            if translated_json.startswith('json'):
                                translated_json = translated_json[4:].strip()
                            translated_chunk = json.loads(translated_json)
                            logging.debug("  - JSON успешно распарсен после очистки")
                        
                        if not translated_chunk:
                            raise ValueError("Получен пустой ответ от API")
                            
                        translated_chunks.append(translated_chunk)
                        chunk_translated = True
                        logging.info(f"Часть {i}/{len(chunks)} успешно переведена")
                        
                        if i < len(chunks):
                            wait_time = 61
                            logging.debug(f"Ожидание {wait_time} секунд перед следующим запросом...")
                            time.sleep(wait_time)
                        
                        break

                    except Exception as e:
                        response_headers = getattr(e, 'response', None)
                        headers = response_headers.headers if response_headers else {}
                        logging.debug(f"\nОшибка при попытке {attempt + 1}:")
                        logging.debug(f"  - Тип ошибки: {type(e).__name__}")
                        logging.debug(f"  - Сообщение: {str(e)}")
                        if headers:
                            logging.debug("  - Заголовки ответа:")
                            for key, value in headers.items():
                                logging.debug(f"    {key}: {value}")
                        
                        self._handle_api_error(e, attempt, headers)
                        if attempt == self.max_retries - 1:
                            raise

                if not chunk_translated:
                    raise Exception(f"Не удалось перевести часть {i} после {self.max_retries} попыток")

            # Объединяем все переведенные части
            if len(translated_chunks) == 1:
                return translated_chunks[0]
            else:
                result = {}
                for chunk in translated_chunks:
                    for key, value in chunk.items():
                        if "_part_" in key:
                            base_key = key.split("_part_")[0]
                            if base_key not in result:
                                result[base_key] = ""
                            result[base_key] += value
                        else:
                            result[key] = value
                return result

        except Exception as e:
            logging.exception(f"Критическая ошибка при переводе: {str(e)}")
            raise

