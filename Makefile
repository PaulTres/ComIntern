.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help message
	@echo "Usage: make [command]"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

.PHONY: sync
sync: ## Install the Python dependencies into .venv
	uv sync

.PHONY: infra
infra: ## Start PostgreSQL and Qdrant for local development
	docker compose -f dev/docker-compose.yml up -d

.PHONY: infra-down
infra-down: ## Stop PostgreSQL and Qdrant (data is kept)
	docker compose -f dev/docker-compose.yml down

.PHONY: migrate
migrate: ## Create or update the tables
	uv run alembic upgrade head

.PHONY: seed
seed: ## Load the catalog into PostgreSQL and index it and regulation_texts/ into Qdrant
	uv run comintern-seed

.PHONY: run
run: ## Run the API on RUN__HOST:RUN__PORT
	uv run comintern

.PHONY: dev
dev: ## Run the API with hot reload
	uv run uvicorn comintern.api.app:create_app --factory --reload --port 8000

.PHONY: test
test: ## Run the tests (no Docker, no Ollama needed)
	uv run pytest

.PHONY: lint
lint: ## Lint with ruff
	uv run ruff check .

.PHONY: format
format: ## Format with ruff
	uv run ruff format .

.PHONY: up
up: ## Build and start the whole stack in Docker
	docker compose up --build -d

.PHONY: down
down: ## Stop the whole stack (data is kept)
	docker compose down
