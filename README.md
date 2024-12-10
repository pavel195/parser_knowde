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

### 2. Запуск парсера
```bash
# Запуск парсера для сбора данных
python main.py
```
Парсер выполнит:
- Сбор ссылок на бренды
- Получение данных о каждом бренде
- Сохранение в JSON файлы в директории data/brand_data/

### 3. Запуск API сервера
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

## Примечание
Перед использованием API необходимо собрать данные с помощью парсера.
