FROM python:3.10-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Установка Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Установка pipenv
RUN pip install pipenv

# Создание рабочей директории
WORKDIR /app

# Копирование файлов проекта
COPY Pipfile Pipfile.lock ./
COPY scripts ./scripts/
COPY src ./src/
COPY .env ./

# Установка зависимостей через pipenv
RUN pipenv install --deploy --system

# Создание необходимых директорий
RUN mkdir -p /app/data/brand_data /app/data/products /app/data/pipeline /app/data/logs

# Запуск pipeline.py
CMD ["python", "scripts/pipeline.py"] 