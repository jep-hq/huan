.PHONY: help dev prod up down logs restart clean secrets setup-dev setup-prod health validate

# Docker command (use sudo if user is not in docker group)
DOCKER_CMD := $(shell docker ps >/dev/null 2>&1 && echo "docker" || echo "sudo docker")
COMPOSE_CMD := $(DOCKER_CMD) compose

# Default target
help:
	@echo "HUAN - Docker Compose Management"
	@echo ""
	@echo "Setup Commands:"
	@echo "  make setup-dev     - Set up development environment"
	@echo "  make setup-prod    - Set up production environment"
	@echo "  make secrets       - Generate secure secrets"
	@echo "  make validate      - Validate .env configuration"
	@echo ""
	@echo "Development Commands:"
	@echo "  make dev           - Start development stack"
	@echo "  make logs          - View logs (dev)"
	@echo "  make restart       - Restart all services (dev)"
	@echo ""
	@echo "Production Commands:"
	@echo "  make prod          - Start production stack"
	@echo "  make prod-logs     - View logs (prod)"
	@echo "  make prod-restart  - Restart all services (prod)"
	@echo ""
	@echo "Common Commands:"
	@echo "  make down          - Stop all services"
	@echo "  make clean         - Stop and remove all volumes (⚠️  DATA LOSS)"
	@echo "  make health        - Check service health"
	@echo "  make ps            - List running containers"
	@echo ""

# Setup Commands
setup-dev:
	@echo "Setting up development environment..."
	@if [ ! -f .env ]; then \
		cp .env.development .env; \
		echo "✅ Created .env from .env.development"; \
		echo "⚠️  Remember to update AUTHENTIK_CLIENT_ID and AUTHENTIK_CLIENT_SECRET after first run"; \
	else \
		echo "⚠️  .env already exists, skipping..."; \
	fi

setup-prod:
	@echo "Setting up production environment..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Created .env from .env.example"; \
		echo ""; \
		echo "🔐 Generating secure secrets..."; \
		./generate-secrets.sh; \
		echo ""; \
		echo "⚠️  IMPORTANT: Update .env with:"; \
		echo "  1. Generated secrets above"; \
		echo "  2. AUTHENTIK_CLIENT_ID and AUTHENTIK_CLIENT_SECRET"; \
		echo "  3. Production URLs and domains"; \
	else \
		echo "⚠️  .env already exists, skipping..."; \
	fi

secrets:
	@echo "Generating secure secrets..."
	@./generate-secrets.sh

validate:
	@./validate-env.sh

# Development Commands
dev:
	@echo "Starting development stack..."
	$(COMPOSE_CMD) up -d
	@echo ""
	@echo "✅ Services started!"
	@echo ""
	@echo "📊 Service URLs:"
	@echo "  Frontend:    http://localhost:3000"
	@echo "  Backend:     http://localhost:8001"
	@echo "  Authentik:   http://localhost:9000"
	@echo "  Flower:      http://localhost:5555"
	@echo "  Spark UI:    http://localhost:8081"
	@echo ""
	@echo "View logs: make logs"

logs:
	$(COMPOSE_CMD) logs -f

restart:
	@echo "Restarting all services..."
	$(COMPOSE_CMD) restart
	@echo "✅ Services restarted"

# Production Commands
prod:
	@echo "Starting production stack..."
	@if [ ! -f .env ]; then \
		echo "❌ Error: .env file not found"; \
		echo "Run 'make setup-prod' first"; \
		exit 1; \
	fi
	@echo "Validating environment configuration..."
	@./validate-env.sh || exit 1
	$(COMPOSE_CMD) -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "✅ Production stack started"

prod-logs:
	$(COMPOSE_CMD) -f docker-compose.yml -f docker-compose.prod.yml logs -f

prod-restart:
	@echo "Restarting production services..."
	$(COMPOSE_CMD) -f docker-compose.yml -f docker-compose.prod.yml restart
	@echo "✅ Services restarted"

# Common Commands
down:
	@echo "Stopping all services..."
	$(COMPOSE_CMD) down
	@echo "✅ Services stopped"

clean:
	@echo "⚠️  WARNING: This will delete all data (databases, volumes, etc.)"
	@read -p "Are you sure? (type 'yes' to confirm): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		$(COMPOSE_CMD) down -v; \
		echo "✅ Cleaned up all services and volumes"; \
	else \
		echo "❌ Cancelled"; \
	fi

health:
	@echo "Checking service health..."
	@$(COMPOSE_CMD) ps

ps:
	@$(COMPOSE_CMD) ps

# Service-specific commands
backend-shell:
	$(COMPOSE_CMD) exec backend bash

frontend-shell:
	$(COMPOSE_CMD) exec frontend sh

db-shell:
	$(COMPOSE_CMD) exec postgres psql -U ${POSTGRES_USER:-huan} -d ${POSTGRES_DB:-huan}

redis-cli:
	$(COMPOSE_CMD) exec redis redis-cli

# Backup and restore
backup-db:
	@echo "Backing up database..."
	@mkdir -p backups
	$(COMPOSE_CMD) exec -T postgres pg_dump -U ${POSTGRES_USER:-huan} ${POSTGRES_DB:-huan} > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "✅ Database backed up to backups/"

restore-db:
	@echo "⚠️  WARNING: This will restore the database"
	@read -p "Enter backup file path: " backup_file; \
	if [ -f "$$backup_file" ]; then \
		$(COMPOSE_CMD) exec -T postgres psql -U ${POSTGRES_USER:-huan} ${POSTGRES_DB:-huan} < $$backup_file; \
		echo "✅ Database restored"; \
	else \
		echo "❌ Backup file not found"; \
	fi
