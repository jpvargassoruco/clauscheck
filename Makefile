DC := docker compose -f infra/docker-compose.yml --env-file .env

.PHONY: up up-app down logs ps psql backup restore seed

up:
	@mkdir -p infra/data/postgres infra/data/redis infra/data/caddy/data infra/data/caddy/config
	@mkdir -p infra/data/paperless/data infra/data/paperless/media infra/data/paperless/export infra/data/paperless/consume
	$(DC) up -d

up-app:
	$(DC) --profile app up -d

down:
	$(DC) down

logs:
	$(DC) logs -f --tail=200

ps:
	$(DC) ps

psql:
	$(DC) exec postgres psql -U postgres -d clauscheck

backup:
	./infra/backup.sh

restore:
	./infra/restore.sh $(TS)

seed:
	$(DC) --profile app run --rm api python -m app.seed
