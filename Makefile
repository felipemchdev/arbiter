.PHONY: up down build test lint ps logs seed

up:
	docker compose up -d

down:
	docker compose down

build:
	cd arbiter-dashboard && npm run build

test:
	cd arbiter-api && pytest app/tests/ -v

lint:
	cd arbiter-api && ruff check app/

ps:
	docker compose ps

logs:
	docker compose logs -f

seed:
	docker compose exec api python -m app.scripts.seed_dev
