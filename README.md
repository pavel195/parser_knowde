# Knowde Brand Parser

Парсер и анализатор данных о брендах с платформы Knowde.com. Проект собирает, хранит и анализирует информацию о брендах и их продуктах.

## Установка и запуск

### 1. Установка зависимостей
```bash
# Создание виртуального окружения
python -m venv .venv
source .venv/bin/activate  # Linux/Mac

# Установка зависимостей
pip install -r requirements.txt
```

### 2. Установка Chrome и ChromeDriver

#### Linux
```bash
# Создание директорий
mkdir -p ~/chrome-linux64
mkdir -p ~/chromedriver-linux64

# Скачивание и распаковка Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt-get install -f

# Скачивание и установка ChromeDriver
# Замените VERSION на актуальную версию с https://chromedriver.chromium.org/downloads
wget https://chromedriver.storage.googleapis.com/VERSION/chromedriver_linux64.zip
unzip chromedriver_linux64.zip -d ~/chromedriver-linux64/
chmod +x ~/chromedriver-linux64/chromedriver
```

#### MacOS
```bash
# Установка через Homebrew
brew install --cask google-chrome
brew install --cask chromedriver
```

#### Windows
1. Скачайте Chrome с официального сайта: https://www.google.com/chrome/
2. Скачайте ChromeDriver с: https://chromedriver.chromium.org/downloads
   - Версия ChromeDriver должна соответствовать версии Chrome
3. Распакуйте chromedriver.exe в удобную директорию
4. Добавьте путь к ChromeDriver в переменную PATH



### 3. Запуск парсера
```bash
# Запуск парсера для сбора данных
python main.py
```
Парсер выполнит:
- Сбор ссылок на бренды
- Получение данных о каждом бренде
- Сохранение в JSON файлы в директории data/brand_data/

### 4. Запуск API сервера
```bash
# Запуск API сервера
python scripts/run_api.py
```

API будет доступен по адресу: http://localhost:8000

## API Endpoints

# Список всех брендов
GET /brands/

# Данные конкретного бренда
GET /brands/{brand_name}
GET /brands/{brand_name}?include_products=true

# Сводка о бренде
GET /brands/{brand_name}/summary

# Поиск продуктов
GET /brands/{brand_name}/products
GET /brands/{brand_name}/products?category=Surfactants&keyword=natural

Swagger документация доступна по адресу: http://localhost:8000/docs

## Примечания
- Перед использованием API необходимо собрать данные с помощью парсера
- Убедитесь, что версии Chrome и ChromeDriver совпадают
- При проблемах с доступом к ChromeDriver проверьте права доступа к файлу
