.PHONY: dev prod dev-down prod-down logs migration migrate test lint format migrate-down

dev:
	docker compose -f docker-compose.yaml -f docker-compose.dev.yaml up --build

prod:
	docker compose -f docker-compose.yaml -f docker-compose.prod.yaml up -d --build

dev-down:
	docker compose -f docker-compose.yaml -f docker-compose.dev.yaml down

prod-down:
	docker compose -f docker-compose.yaml -f docker-compose.prod.yaml down

logs:
	docker compose -f docker-compose.yaml -f docker-compose.dev.yaml logs -f

migration:
	docker exec slouka-bot alembic revision --autogenerate -m "$(m)"

migrate:
	docker exec slouka-bot alembic upgrade head

migrate-down:
	docker exec slouka-bot alembic downgrade -1

test:
	cd bot && uv run pytest tests -v

lint:
	cd bot && uv run ruff check src tests && uv run ruff format --check src tests && uv run mypy src

format:
	cd bot && uv run ruff format src tests
