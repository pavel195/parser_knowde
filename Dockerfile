FROM python:3.10-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    build-essential \
    python3-dev \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*



WORKDIR /app

# Копирование файлов зависимостей
COPY Pipfile Pipfile.lock ./

# Установка pipenv и зависимостей
RUN pip install --no-cache-dir pipenv && \
    pipenv install --deploy --system

# Копирование кода приложения
COPY src/ src/
COPY scripts/ scripts/
COPY .env .

# Настройка переменных окружения
ENV PYTHONPATH=/app
ENV DISPLAY=:99
ENV HEADLESS=1
ENV PYTHONUNBUFFERED=1
ENV SELENIUM_DRIVER_CHROME_ARGS="--no-sandbox --headless --disable-gpu --disable-dev-shm-usage"