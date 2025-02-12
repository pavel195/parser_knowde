

## Сервисы

- `knowdie_parser` - Сервис для парсинга и обработки данных
- `ai_translator` - Сервис для перевода текста

## Команды

### Общие команды

```bash
# Сборка всех сервисов
make build

# Запуск всех сервисов
make up

# Остановка всех сервисов
make down

# Просмотр логов всех сервисов
make logs

# Проверка статуса сервисов
make ps
```

### Команды для knowdie_parser

```bash
# Сборка сервиса
make parser-build

# Запуск сервиса
make parser-up

# Остановка сервиса
make parser-down

# Просмотр логов сервиса
make parser-logs

# Запуск парсера брендов
make run-parser

# Запуск извлечения продуктов
make extract-products

# Запуск тестов
make test

# Проверка кода линтером
make lint

# Очистка временных файлов
make clean
```

### Команды для ai_translator

```bash
# Сборка сервиса
make translator-build

# Запуск сервиса
make translator-up

# Остановка сервиса
make translator-down

# Просмотр логов сервиса
make translator-logs
```


