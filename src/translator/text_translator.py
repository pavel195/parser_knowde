"""Интерфейс для перевода через OpenAI"""
import os
import json
from typing import Dict, Any
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()

class TextTranslator:
    def __init__(self):

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY не найден в переменных окружения")
            
        # Инициализация клиента OpenAI
        self.client = OpenAI(api_key=api_key)
        

        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
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

    def translate(self, data: Any) -> Any:
        if not data:
            return data

        try:
            # Преобразуем данные в JSON
            data_json = json.dumps(data, ensure_ascii=False)

            # Отправляем запрос в OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_message},
                    {"role": "user", "content": data_json}
                ],
                temperature=0.3
            )

            # Получаем и парсим ответ
            translated_json = response.choices[0].message.content.strip()
            try:
                translated_data = json.loads(translated_json)
                # Проверяем, что получили валидный ответ
                if not translated_data:
                    raise ValueError("Получен пустой ответ от OpenAI")
                return translated_data
            except json.JSONDecodeError as e:
                print(f"Ошибка при парсинге JSON ответа: {str(e)}")
                raise
            except Exception as e:
                print(f"Ошибка при обработке ответа: {str(e)}")
                raise

        except Exception as e:
            print(f"Ошибка при переводе: {str(e)}")
            raise  

