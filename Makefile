.PHONY: up down build logs backend-shell frontend-shell test migrate seed

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

backend-shell:
	docker compose exec backend bash

frontend-shell:
	docker compose exec frontend sh

test:
	docker compose exec backend pytest

migrate:
	docker compose exec backend alembic upgrade head

seed:
	docker compose exec backend python -m app.seed
