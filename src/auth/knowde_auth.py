"""Модуль для авторизации на сайте Knowde."""
import os
import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict
import time
from faker import Faker
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth

class KnowdeAuth:
    def __init__(self, session_dir: str = "data/sessions"):
        self.faker = Faker()
        self.driver = None
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = self.session_dir / "knowde_session.pkl"
        self.setup_chrome_options()
        
    def setup_chrome_options(self):
        """Настройка опций Chrome"""
        self.chrome_options = Options()
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-gpu")
        
        # Антидетект настройки
        self.chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        self.chrome_options.add_argument(f'--user-agent={self.faker.chrome()}')
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)

    def load_session(self) -> Optional[Dict]:
        """Загрузка сохраненной сессии"""
        try:
            if not self.session_file.exists():
                return None
                
            with open(self.session_file, 'rb') as f:
                session_data = pickle.load(f)
                
            # Проверяем срок действия сессии (24 часа)
            if datetime.now() - session_data['timestamp'] > timedelta(hours=24):
                return None
                
            return session_data
        except Exception as e:
            print(f"Ошибка при загрузке сессии: {e}")
            return None

    def save_session(self, session_data: Dict) -> None:
        """Сохранение сессии"""
        try:
            session_data['timestamp'] = datetime.now()
            with open(self.session_file, 'wb') as f:
                pickle.dump(session_data, f)
        except Exception as e:
            print(f"Ошибка при сохранении сессии: {e}")

    def get_auth_session(self, email: str, password: str, force_new: bool = False) -> Optional[Dict]:
        """
        Получение авторизованной сессии.
        Args:
            email: Email для входа
            password: Пароль
            force_new: Принудительное создание новой сессии
        Returns:
            Dict: Данные сессии и драйвер или None при ошибке
        """
        if not force_new:
            session = self.load_session()
            if session:
                print("Используется сохраненная сессия")
                # Создаем новый драйвер с сохраненными куками
                if self._init_driver():
                    self.driver.get("https://www.knowde.com")
                    for cookie in session['cookies']:
                        self.driver.add_cookie(cookie)
                    self.driver.refresh()
                    return {'driver': self.driver, **session}
                return None

        try:
            auth_data = self._perform_login(email, password)
            if auth_data:
                self.save_session(auth_data)
                return {'driver': self.driver, **auth_data}
            return None
            
        except Exception as e:
            print(f"Ошибка при получении сессии: {e}")
            if self.driver:
                self.driver.quit()
            return None

    def _perform_login(self, email: str, password: str) -> Optional[Dict]:
        """Выполнение процесса авторизации"""
        try:
            if not self._init_driver():
                return None

            self.driver.get("https://www.knowde.com")
            self._random_delay(1.5, 3.0)
            
            # Нажимаем кнопку Sign In
            sign_in_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='sign-in-button']"))
            )
            sign_in_button.click()
            self._random_delay()
            
            # Вводим email
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='email'][class^='input_input']"))
            )
            self._type_like_human(email_input, email)
            
            # Нажимаем Continue
            continue_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit'][class^='auth-modal-continue-button']"))
            )
            continue_button.click()
            self._random_delay()
            
            # Вводим пароль
            password_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password'][class^='input_input']"))
            )
            self._type_like_human(password_input, password)
            
            # Нажимаем кнопку входа
            submit_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit'][class^='auth-modal-continue-button']"))
            )
            submit_button.click()
            
            # Ждем успешной авторизации
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-testid='account-pill']"))
            )
            
            # Получаем cookies и user-agent
            cookies = self.driver.get_cookies()
            user_agent = self.driver.execute_script("return navigator.userAgent")
            
            auth_data = {
                'cookies': cookies,
                'user_agent': user_agent
            }
            
            return auth_data
            
        except Exception as e:
            print(f"Ошибка при авторизации: {e}")
            if self.driver:
                self.driver.quit()
            return None

    def _init_driver(self) -> bool:
        """Инициализация драйвера Chrome"""
        try:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            stealth(self.driver,
                   languages=["en-US", "en"],
                   vendor="Google Inc.",
                   platform="Win32",
                   webgl_vendor="Intel Inc.",
                   renderer="Intel Iris OpenGL Engine",
                   fix_hairline=True,
                   )
            return True
        except Exception as e:
            print(f"Ошибка при инициализации драйвера: {e}")
            return False

    def _random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
        """Случайная задержка для имитации человеческого поведения"""
        time.sleep(self.faker.pyfloat(min_value=min_seconds, max_value=max_seconds, right_digits=2))

    def _type_like_human(self, element, text: str) -> None:
        """Имитация человеческого набора текста"""
        for char in text:
            element.send_keys(char)
            self._random_delay(0.1, 0.3) 