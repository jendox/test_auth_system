HOST ?= "127.0.0.1"
PORT ?= 8000
UV ?= uv

lint: ## Проверяет линтерами код в репозитории
	$(UV) run ruff check ./src

fmt: ## Запуск автоформатера
	$(UV) run ruff check --fix ./src

run: ## Запуск сервера uvicorn
	PYTHONPATH=. $(UV) run uvicorn src.main:app --host $(HOST) --port $(PORT) --reload

up: ## Поднять окружение
	$(UV) run docker-compose up -d

down: ## Завершить работу окружения
	$(UV) run docker-compose down

makemigrations: ## Создание миграции (использование: make migrations MESSAGE="Init migration")
	$(UV) run alembic revision --autogenerate -m "$(MESSAGE)"

migrate: ## Применение миграции
	$(UV) run alembic upgrade head

downgrade: ## Откат миграции
	$(UV) run alembic downgrade -1

token: ## Генерация токена (использование: make token LENGTH=64 (по умолчанию 32))
	head -c $(or $(LENGTH),32) /dev/urandom | base64 | tr -d '/+=' | cut -c1-$(or $(LENGTH),32)

list: ## Отображает список доступных команд и их описания
	@echo "Cписок доступных команд:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
