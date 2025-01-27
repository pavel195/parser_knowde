import os
import json
import openai
from dotenv import load_dotenv
from typing import Dict, List

load_dotenv()

class TextTranslator:
    def __init__(self):
        # Получаем ключ API из переменных окружения
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY не найден в переменных окружения")

        
        openai.api_key = api_key

        
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4')

        
        self.system_message = os.getenv('TRANSLATOR_MESSAGE', 
            "Hey, we are going translating chemical raw material description from English to Russian. "
            "I will send you one-by-one JSONs containing material description. Your aim is to respond with JSONs "
            "where keys are the same as in input, and the values are translated data. Use chemical professional vocabulary."
        )

    def translate_json(self, data: Dict) -> Dict:
        """
        Переводит JSON данные о химическом продукте.

        Args:
            data: JSON данные для перевода
        Returns:
            Dict: Переведенные данные с сохранением структуры
        """
        if not data:
            return data

        try:
            # Преобразуем данные в строку JSON
            data_json = json.dumps(data, ensure_ascii=False)

            # Отправляем запрос в OpenAI
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_message},
                    {"role": "user", "content": data_json}
                ],
                temperature=0.3
            )

            # Получаем ответ
            translated_json = response['choices'][0]['message']['content'].strip()
            
            try:
                return json.loads(translated_json)
            except json.JSONDecodeError as e:
                print(f"Ошибка при парсинге JSON ответа: {str(e)}")
                return data

        except Exception as e:
            print(f"Ошибка при переводе JSON: {str(e)}")
            return data

    def translate_text(self, text: str) -> str:
        """
        Переводит отдельный текст, оборачивая его в JSON.

        Args:
            text: Текст для перевода
        Returns:
            str: Переведенный текст
        """
        if not text or not isinstance(text, str):
            return text

        try:
            # Оборачиваем текст в JSON
            data = {"text": text}
            translated = self.translate_json(data)
            return translated.get("text", text)
        except Exception as e:
            print(f"Ошибка при переводе текста: {str(e)}")
            return text

    def translate_list(self, items: List) -> List:
        """
        Переводит список, оборачивая его в JSON.

        Args:
            items: Список для перевода
        Returns:
            List: Переведенный список
        """
        if not items or not isinstance(items, list):
            return items

        try:
            # Оборачиваем список в JSON
            data = {"items": items}
            translated = self.translate_json(data)
            return translated.get("items", items)
        except Exception as e:
            print(f"Ошибка при переводе списка: {str(e)}")
            return items
