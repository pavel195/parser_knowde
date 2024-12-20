"""Модуль для авторизации на сайте Knowde."""
import os
import time
from faker import Faker
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from typing import Optional, Dict

class KnowdeAuth:
    def __init__(self):
        self.faker = Faker()
        self.driver = None
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

        # Дополнительные настройки для обхода блокировок
        self.chrome_options.add_argument('--disable-infobars')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-browser-side-navigation')
        self.chrome_options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        
        # Настройка языка и разрешения
        self.chrome_options.add_argument('--lang=en-US,en;q=0.9')
        self.chrome_options.add_argument('--window-size=1920,1080')

    def get_auth_session(self, email: str, password: str) -> Optional[Dict]:
        """
        Выполнение авторизации и получение сессии.
        Args:
            email: Email для входа
            password: Пароль
        Returns:
            Dict: Данные сессии и драйвер или None при ошибке
        """
        try:
            if not self._init_driver():
                return None

            print("Начинаем процесс авторизации...")
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
            
            print("Авторизация успешно выполнена")
            
            # Получаем cookies и user-agent
            cookies = self.driver.get_cookies()
            user_agent = self.driver.execute_script("return navigator.userAgent")
            
            return {
                'driver': self.driver,
                'cookies': cookies,
                'user_agent': user_agent
            }
            
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