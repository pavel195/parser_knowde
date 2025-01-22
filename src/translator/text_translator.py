"""Модуль для перевода текста с поддержкой нескольких переводчиков."""
import time
import os
import requests
from typing import List, Optional
from enum import Enum
from deep_translator import (
    GoogleTranslator,
    MyMemoryTranslator
)

class TranslatorType(Enum):
    LIBRE = "libre"
    GOOGLE = "google"


class TextTranslator:
    # Маппинг языковых кодов для разных переводчиков
    LANGUAGE_CODES = {
        'en': {
            'google': 'en',
            'mymemory': 'en-GB',
            'libre': 'en'
        },
        'ru': {
            'google': 'ru',
            'mymemory': 'ru-RU',
            'libre': 'ru'
        }
    }

    # Символы, которые не нужно переводить
    SKIP_CHARS = {'-', '%', '°', '®', '™', '©'}

    def __init__(self, source_lang: str = 'en', target_lang: str = 'ru', libre_host: str = 'http://localhost:5000'):
        """
        Инициализация переводчика.
        
        Args:
            source_lang: Исходный язык
            target_lang: Целевой язык
            libre_host: Адрес LibreTranslate сервера
        """
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.libre_host = libre_host
        self._initialize_translators()
        self.current_translator_idx = 0
        self.retry_delay = 1  # секунды между попытками
        self.max_retries = 3  # максимальное количество попыток для каждого переводчика

    def _get_language_code(self, lang: str, translator_type: str) -> str:
        """Возвращает правильный код языка для конкретного переводчика."""
        return self.LANGUAGE_CODES.get(lang, {}).get(translator_type, lang)

    def _initialize_translators(self):
        """Инициализация всех доступных переводчиков."""
        self.translators = []

        # LibreTranslate (локальный сервер)
        try:
            # Проверяем доступность сервера
            response = requests.get(f"{self.libre_host}/languages")
            if response.status_code == 200:
                self.translators.append({
                    'type': TranslatorType.LIBRE,
                    'instance': None  # Не нужен инстанс, будем использовать API напрямую
                })
                print("Инициализирован локальный LibreTranslate сервер")
        except Exception as e:
            print(f"Ошибка инициализации LibreTranslate: {str(e)}")
        
        # Google Translator
        try:
            self.translators.append({
                'type': TranslatorType.GOOGLE,
                'instance': GoogleTranslator(
                    source=self._get_language_code(self.source_lang, 'google'),
                    target=self._get_language_code(self.target_lang, 'google')
                )
            })
        except Exception as e:
            print(f"Ошибка инициализации Google переводчика: {str(e)}")

        # MyMemory Translator
        try:
            self.translators.append({
                'type': TranslatorType.MYMEMORY,
                'instance': MyMemoryTranslator(
                    source=self._get_language_code(self.source_lang, 'mymemory'),
                    target=self._get_language_code(self.target_lang, 'mymemory')
                )
            })
        except Exception as e:
            print(f"Ошибка инициализации MyMemory переводчика: {str(e)}")

    def _translate_with_libre(self, text: str) -> Optional[str]:
        """
        Переводит текст с помощью локального LibreTranslate сервера.
        
        Args:
            text: Текст для перевода
        Returns:
            Optional[str]: Переведенный текст или None в случае ошибки
        """
        try:
            response = requests.post(
                f"{self.libre_host}/translate",
                json={
                    "q": text,
                    "source": self._get_language_code(self.source_lang, 'libre'),
                    "target": self._get_language_code(self.target_lang, 'libre')
                }
            )
            if response.status_code == 200:
                return response.json()['translatedText']
        except Exception as e:
            print(f"Ошибка перевода через LibreTranslate: {str(e)}")
        return None

    def _should_skip_translation(self, text: str) -> bool:
        """Проверяет, нужно ли пропустить перевод текста."""
        return (
            not text or 
            not isinstance(text, str) or 
            text.strip() in self.SKIP_CHARS or
            all(char in self.SKIP_CHARS for char in text.strip())
        )

    def _try_translate(self, text: str, translator_info: dict) -> Optional[str]:
        """
        Пытается перевести текст с помощью конкретного переводчика.
        
        Args:
            text: Текст для перевода
            translator_info: Информация о переводчике
        Returns:
            Optional[str]: Переведенный текст или None в случае ошибки
        """
        if self._should_skip_translation(text):
            return text

        for attempt in range(self.max_retries):
            try:
                if translator_info['type'] == TranslatorType.LIBRE:
                    return self._translate_with_libre(text)
                else:
                    return translator_info['instance'].translate(text)
            except Exception as e:
                print(f"Ошибка перевода ({translator_info['type'].value}, попытка {attempt + 1}): {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
        return None

    def translate_text(self, text: str) -> str:
        """
        Переводит текст, используя доступные переводчики.
        
        Args:
            text: Исходный текст
        Returns:
            str: Переведенный текст
        """
        if self._should_skip_translation(text):
            return text

        # Пробуем все доступные переводчики
        for _ in range(len(self.translators)):
            translator_info = self.translators[self.current_translator_idx]
            result = self._try_translate(text, translator_info)
            
            if result:
                return result
            
            # Переключаемся на следующий переводчик
            self.current_translator_idx = (self.current_translator_idx + 1) % len(self.translators)
            time.sleep(self.retry_delay)  # Пауза перед использованием следующего переводчика

        print(f"Не удалось перевести текст после всех попыток: {text}")
        return text

    def translate_list(self, items: List) -> List:
        """
        Переводит список значений.
        
        Args:
            items: Список для перевода
        Returns:
            List: Переведенный список
        """
        return [self.translate_text(item) for item in items] 