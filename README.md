# Knowde Brand Parser

Парсер и анализатор данных о брендах с платформы Knowde.com. Проект собирает, хранит и анализирует информацию о брендах и их продуктах.

## Установка и запуск

### 1. Установка зависимостей
```bash
# Создание виртуального окружения
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate  # Windows

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
3. Распакуйте chromedriver.exe в удобную ��иректорию
4. Добавьте путь к ChromeDriver в переменную PATH

### 3. Настройка окружения
Создайте файл .env на основе .env.example:
```bash
cp .env.example .env
```

### 4. Запуск парсера
```bash
# Запуск парсера для сбора данных
python scripts/run_parser.py
```

Парсер выполнит:
- Сбор ссылок на бренды
- Получение данных о каждом бренде
- Сохранение в JSON файлы в директории data/brand_data/

### 5. Извлечение данных о продуктах
```bash
# Запуск извлечения продуктов
python scripts/extract_products.py
```

Скрипт создаст отдельные JSON файлы для каждого продукта в директории data/products/{brand_name}/

## Структура проекта
```
knowde_parser/
├── src/
│   ├── api/              # API endpoints
│   ├── parser/           # Парсер брендов
│   ├── processor/        # Обработка данных
│   ├── service/          # Бизнес-логика
│   └── storage/          # Работа с хранилищем
├── data/
│   ├── brand_data/       # JSON файлы брендов
│   └── products/         # JSON файлы продуктов
├── scripts/              # Скрипты
└── tests/                # Тесты
```

## Примечания
- Перед запуском убедитесь, что Chrome и ChromeDriver установлены и доступны
- Проверьте соответствие версий Chrome и ChromeDriver
- При проблемах с доступом к ChromeDriver проверьте права доступа к файлу
- Данные сохраняются в директории data/
