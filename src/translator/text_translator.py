"""Интерфейс для перевода через OpenAI"""
import os
import json
import time
from typing import Dict, Any
from openai import OpenAI
from openai.types.error import APIError
from dotenv import load_dotenv


load_dotenv()

class TextTranslator:
    def __init__(self):

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY не найден в переменных окружения")
            
        # Инициализация клиента OpenAI
        self.client = OpenAI(api_key=api_key)
        

        self.model = os.getenv("OPENAI_MODEL", "gpt-4")
        self.max_retries = 3
        self.retry_delay = 5
        self.max_tokens = 1000  # Максимальное количество токенов для gpt-4
        
        print(f"Используется модель: {self.model}")

        # Базовый промпт для перевода
        self.system_message = os.getenv(
            "TRANSLATOR_MESSAGE",
            (
                "Hey, we are translating chemical raw material descriptions from English to Russian. "
                "I will send you JSONs containing material descriptions one by one. Your task is to respond with JSONs "
                "where keys remain unchanged and values are translated using chemical professional vocabulary."
            )
        )

    def _handle_api_error(self, e: Exception, attempt: int) -> None:
        """Обработка ошибок API с логированием"""
        if isinstance(e, APIError):
            print(f"OpenAI API ошибка (попытка {attempt + 1}/{self.max_retries}): {str(e)}")
            if e.status_code == 429:  # Rate limit
                time.sleep(self.retry_delay * 2)  # Увеличенная задержка при rate limit
            else:
                time.sleep(self.retry_delay)
        else:
            print(f"Неожиданная ошибка (попытка {attempt + 1}/{self.max_retries}): {str(e)}")
            time.sleep(self.retry_delay)

    def _chunk_json(self, data: Dict) -> list:
        """Разбивает большой JSON на части, если он превышает лимит токенов"""
        data_str = json.dumps(data, ensure_ascii=False)
        if len(data_str) > self.max_tokens * 2:  # Примерная оценка
            result = []
            # Разбиваем на части по основным ключам
            temp_dict = {}
            current_size = 0
            for key, value in data.items():
                value_str = json.dumps({key: value}, ensure_ascii=False)
                if current_size + len(value_str) > self.max_tokens * 2:
                    if temp_dict:
                        result.append(temp_dict)
                        temp_dict = {}
                        current_size = 0
                temp_dict[key] = value
                current_size += len(value_str)
            if temp_dict:
                result.append(temp_dict)
            return result
        return [data]

    def translate(self, data: Any) -> Any:
        """
        Универсальный метод перевода данных любого типа.
        
        Args:
            data: Данные для перевода (любого типа)
        Returns:
            Any: Переведенные данные того же типа
        """
        if not data:
            return data

        try:
            # Разбиваем данные на части, если они слишком большие
            chunks = self._chunk_json(data)
            translated_chunks = []

            for chunk in chunks:
                chunk_translated = False
                data_json = json.dumps(chunk, ensure_ascii=False)

                for attempt in range(self.max_retries):
                    try:
                        response = self.client.chat.completions.create(
                            model=self.model,
                            messages=[
                                {"role": "system", "content": self.system_message},
                                {"role": "user", "content": data_json}
                            ],
                            temperature=0.3
                        )

                        translated_json = response.choices[0].message.content.strip()
                        translated_chunk = json.loads(translated_json)
                        
                        if not translated_chunk:
                            raise ValueError("Получен пустой ответ от OpenAI")
                            
                        translated_chunks.append(translated_chunk)
                        chunk_translated = True
                        break

                    except Exception as e:
                        self._handle_api_error(e, attempt)
                        if attempt == self.max_retries - 1:
                            raise

                if not chunk_translated:
                    raise Exception(f"Не удалось перевести часть данных после {self.max_retries} попыток")

            # Объединяем все переведенные части
            if len(translated_chunks) == 1:
                return translated_chunks[0]
            else:
                result = {}
                for chunk in translated_chunks:
                    result.update(chunk)
                return result

        except Exception as e:
            print(f"Критическая ошибка при переводе: {str(e)}")
            raise  

