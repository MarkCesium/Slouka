.PHONY: dev down logs migration migrate

dev:
	docker compose -f docker-compose.yaml -f docker-compose.dev.yaml up --build

down:
	docker compose -f docker-compose.yaml -f docker-compose.dev.yaml down

logs:
	docker compose -f docker-compose.yaml -f docker-compose.dev.yaml logs -f

migration:
	docker exec slouka-bot uv run alembic revision --autogenerate -m "$(m)"

migrate:
	docker exec slouka-bot uv run alembic upgrade head
