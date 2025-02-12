# Переменные
DOCKER_COMPOSE = docker-compose
DOCKER = docker


GREEN = \033[0;32m
RED = \033[0;31m
YELLOW = \033[0;33m
NC = \033[0m 

.PHONY: help build up down restart logs ps clean init-db status

help: 
	@echo "Доступные команды:"
	@echo "${GREEN}make build${NC}      - Собрать все контейнеры"
	@echo "${GREEN}make up${NC}         - Запустить все сервисы"
	@echo "${GREEN}make down${NC}       - Остановить все сервисы"
	@echo "${GREEN}make restart${NC}    - Перезапустить все сервисы"
	@echo "${GREEN}make logs${NC}       - Показать логи (используйте service=имя_сервиса для конкретного сервиса)"
	@echo "${GREEN}make ps${NC}         - Показать статус контейнеров"
	@echo "${GREEN}make clean${NC}      - Очистить все данные (контейнеры, образы, тома)"
	@echo "${GREEN}make init-db${NC}    - Инициализировать базу данных"
	@echo "${GREEN}make status${NC}     - Проверить статус всех сервисов"

build: ## Собрать все контейнеры
	@echo "${YELLOW}Сборка контейнеров...${NC}"
	$(DOCKER_COMPOSE) build --no-cache

up: 
	@echo "${YELLOW}Запуск сервисов...${NC}"
	$(DOCKER_COMPOSE) up -d
	@echo "${GREEN}Сервисы запущены${NC}"
	@make status

down: ## Остановить все сервисы
	@echo "${YELLOW}Остановка сервисов...${NC}"
	$(DOCKER_COMPOSE) down
	@echo "${GREEN}Сервисы остановлены${NC}"

restart: down up ## Перезапустить все сервисы

logs: ## Показать логи (используйте service=имя_сервиса)
ifdef service
	$(DOCKER_COMPOSE) logs -f $(service)
else
	$(DOCKER_COMPOSE) logs -f
endif

ps: ## Показать статус контейнеров
	@echo "${YELLOW}Статус контейнеров:${NC}"
	$(DOCKER_COMPOSE) ps

clean: down ## Очистить все данные
	@echo "${RED}Внимание! Это действие удалит все данные!${NC}"
	@read -p "Вы уверены? [y/N] " confirm && [ $$confirm = "y" ]
	$(DOCKER_COMPOSE) down -v
	$(DOCKER) system prune -af
	$(DOCKER) volume prune -f
	@echo "${GREEN}Очистка завершена${NC}"

init-db: ## Инициализировать базу данных
	@echo "${YELLOW}Инициализация базы данных...${NC}"
	$(DOCKER_COMPOSE) exec pipeline python -c "from src.database.db import init_db; init_db()"
	@echo "${GREEN}База данных инициализирована${NC}"

status: ## Проверить статус всех сервисов
	@echo "${YELLOW}Проверка статуса сервисов...${NC}"
	@echo "\nСтатус контейнеров:"
	@$(DOCKER_COMPOSE) ps
	@echo "\nСтатус базы данных:"
	@$(DOCKER_COMPOSE) exec db pg_isready -U postgres || echo "${RED}База данных недоступна${NC}"
	@echo "\nСтатус API:"
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ || echo "${RED}API недоступен${NC}" 