# Knowde Brand Parser

Парсер и анализатор данных о брендах с платформы Knowde.com.

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

### 2. Установка WebDriver Manager
```bash
# Установка webdriver_manager
pip install webdriver_manager
```

### 3. Запуск скриптов
```bash
# Сбор данных о брендах
python scripts/run_parser.py

# Извлечение данных о продуктах
python scripts/extract_products.py
```

## Структура проекта
```
knowde_parser/
├── src/              # Исходный код
├── data/             # Собранные данные
├── scripts/          # Скрипты запуска
└── tests/            # Тесты
```
