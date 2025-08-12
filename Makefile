# Lawyerless Development Makefile
# Common development tasks for the Lawyerless project

.PHONY: help setup build start stop restart logs clean test format lint check health

# Default target
.DEFAULT_GOAL := help

# Colors
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
RED := \033[31m
RESET := \033[0m

# Project configuration
PROJECT_NAME := lawyerless
BACKEND_DIR := backend
FRONTEND_DIR := frontend
COMPOSE_FILE := docker-compose.yml

help: ## Show this help message
	@echo "$(BLUE)Lawyerless Development Tasks$(RESET)"
	@echo ""
	@echo "$(YELLOW)Setup Commands:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '(setup|install|build)' | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Development Commands:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '(start|stop|restart|logs)' | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Quality Commands:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '(test|format|lint|check)' | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Utility Commands:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -vE '(setup|install|build|start|stop|restart|logs|test|format|lint|check)' | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(RESET) %s\n", $$1, $$2}'

# ==========================================
# Setup Commands
# ==========================================

setup: ## Run complete development environment setup
	@echo "$(BLUE)Setting up Lawyerless development environment...$(RESET)"
	@chmod +x scripts/dev-setup.sh
	@./scripts/dev-setup.sh

setup-quick: ## Quick setup (env files only)
	@echo "$(BLUE)Quick environment setup...$(RESET)"
	@chmod +x scripts/dev-setup.sh
	@./scripts/dev-setup.sh --env-only

install-backend: ## Install backend dependencies
	@echo "$(BLUE)Installing backend dependencies...$(RESET)"
	@cd $(BACKEND_DIR) && python -m venv venv_linux && source venv_linux/bin/activate && pip install -r requirements.txt -r requirements-dev.txt

install-frontend: ## Install frontend dependencies
	@echo "$(BLUE)Installing frontend dependencies...$(RESET)"
	@cd $(FRONTEND_DIR) && npm ci

build: ## Build all Docker images
	@echo "$(BLUE)Building Docker images...$(RESET)"
	@docker-compose build

build-backend: ## Build backend Docker image only
	@echo "$(BLUE)Building backend Docker image...$(RESET)"
	@docker-compose build backend

build-frontend: ## Build frontend Docker image only
	@echo "$(BLUE)Building frontend Docker image...$(RESET)"
	@docker-compose build frontend

# ==========================================
# Development Commands
# ==========================================

start: ## Start all services
	@echo "$(BLUE)Starting all services...$(RESET)"
	@docker-compose up -d
	@echo "$(GREEN)Services started!$(RESET)"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend:  http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"

start-core: ## Start core services only (redis, database)
	@echo "$(BLUE)Starting core services...$(RESET)"
	@docker-compose up -d redis database

start-app: ## Start application services (backend, frontend)
	@echo "$(BLUE)Starting application services...$(RESET)"
	@docker-compose up -d backend frontend

start-monitoring: ## Start with monitoring services
	@echo "$(BLUE)Starting with monitoring...$(RESET)"
	@docker-compose --profile monitoring up -d

stop: ## Stop all services
	@echo "$(BLUE)Stopping all services...$(RESET)"
	@docker-compose down
	@echo "$(GREEN)Services stopped!$(RESET)"

restart: ## Restart all services
	@echo "$(BLUE)Restarting all services...$(RESET)"
	@docker-compose restart
	@echo "$(GREEN)Services restarted!$(RESET)"

restart-backend: ## Restart backend service only
	@echo "$(BLUE)Restarting backend...$(RESET)"
	@docker-compose restart backend

restart-frontend: ## Restart frontend service only
	@echo "$(BLUE)Restarting frontend...$(RESET)"
	@docker-compose restart frontend

# ==========================================
# Logs and Monitoring
# ==========================================

logs: ## Show logs from all services
	@docker-compose logs -f

logs-backend: ## Show backend logs
	@docker-compose logs -f backend

logs-frontend: ## Show frontend logs
	@docker-compose logs -f frontend

logs-redis: ## Show Redis logs
	@docker-compose logs -f redis

logs-db: ## Show database logs
	@docker-compose logs -f database

status: ## Show service status
	@echo "$(BLUE)Service Status:$(RESET)"
	@docker-compose ps

health: ## Check service health
	@echo "$(BLUE)Checking service health...$(RESET)"
	@echo -n "Backend:  "
	@curl -s -f http://localhost:8000/health >/dev/null && echo "$(GREEN)✓ Healthy$(RESET)" || echo "$(RED)✗ Unhealthy$(RESET)"
	@echo -n "Frontend: "
	@curl -s -f http://localhost:3000 >/dev/null && echo "$(GREEN)✓ Healthy$(RESET)" || echo "$(RED)✗ Unhealthy$(RESET)"
	@echo -n "Redis:    "
	@docker-compose exec redis redis-cli ping >/dev/null 2>&1 && echo "$(GREEN)✓ Healthy$(RESET)" || echo "$(RED)✗ Unhealthy$(RESET)"

# ==========================================
# Development Shell Access
# ==========================================

shell-backend: ## Access backend container shell
	@docker-compose exec backend bash

shell-frontend: ## Access frontend container shell
	@docker-compose exec frontend sh

shell-redis: ## Access Redis CLI
	@docker-compose exec redis redis-cli

shell-db: ## Access PostgreSQL shell
	@docker-compose exec database psql -U lawyerless -d lawyerless

# ==========================================
# Testing Commands
# ==========================================

test: ## Run all tests
	@echo "$(BLUE)Running all tests...$(RESET)"
	@$(MAKE) test-backend
	@$(MAKE) test-frontend

test-backend: ## Run backend tests
	@echo "$(BLUE)Running backend tests...$(RESET)"
	@docker-compose exec backend python -m pytest -v

test-backend-coverage: ## Run backend tests with coverage
	@echo "$(BLUE)Running backend tests with coverage...$(RESET)"
	@docker-compose exec backend python -m pytest --cov=app --cov-report=term-missing -v

test-frontend: ## Run frontend tests
	@echo "$(BLUE)Running frontend tests...$(RESET)"
	@docker-compose exec frontend npm test

test-frontend-e2e: ## Run frontend E2E tests
	@echo "$(BLUE)Running frontend E2E tests...$(RESET)"
	@docker-compose exec frontend npm run test:e2e

# ==========================================
# Code Quality Commands
# ==========================================

format: ## Format all code
	@echo "$(BLUE)Formatting code...$(RESET)"
	@$(MAKE) format-backend
	@$(MAKE) format-frontend

format-backend: ## Format backend code
	@echo "$(BLUE)Formatting backend code...$(RESET)"
	@docker-compose exec backend black app/
	@docker-compose exec backend isort app/

format-frontend: ## Format frontend code
	@echo "$(BLUE)Formatting frontend code...$(RESET)"
	@docker-compose exec frontend npm run format

lint: ## Lint all code
	@echo "$(BLUE)Linting code...$(RESET)"
	@$(MAKE) lint-backend
	@$(MAKE) lint-frontend

lint-backend: ## Lint backend code
	@echo "$(BLUE)Linting backend code...$(RESET)"
	@docker-compose exec backend flake8 app/
	@docker-compose exec backend mypy app/

lint-frontend: ## Lint frontend code
	@echo "$(BLUE)Linting frontend code...$(RESET)"
	@docker-compose exec frontend npm run lint

type-check: ## Run type checking
	@echo "$(BLUE)Running type checks...$(RESET)"
	@docker-compose exec backend mypy app/
	@docker-compose exec frontend npm run type-check

security-check: ## Run security checks
	@echo "$(BLUE)Running security checks...$(RESET)"
	@docker-compose exec backend bandit -r app/
	@docker-compose exec backend safety check

# ==========================================
# Database Commands
# ==========================================

db-reset: ## Reset database
	@echo "$(BLUE)Resetting database...$(RESET)"
	@docker-compose down database
	@docker volume rm lawyerless-postgres-data 2>/dev/null || true
	@docker-compose up -d database
	@sleep 5
	@echo "$(GREEN)Database reset complete!$(RESET)"

db-migrate: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(RESET)"
	@docker-compose exec backend alembic upgrade head

db-backup: ## Backup database
	@echo "$(BLUE)Creating database backup...$(RESET)"
	@mkdir -p backups
	@docker-compose exec database pg_dump -U lawyerless lawyerless > backups/lawyerless_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)Database backup created in backups/$(RESET)"

# ==========================================
# Utility Commands
# ==========================================

clean: ## Clean up containers, images, and volumes
	@echo "$(BLUE)Cleaning up...$(RESET)"
	@docker-compose down -v --rmi local --remove-orphans
	@docker system prune -f
	@echo "$(GREEN)Cleanup complete!$(RESET)"

clean-cache: ## Clean application caches
	@echo "$(BLUE)Cleaning caches...$(RESET)"
	@docker-compose exec backend find . -type f -name "*.pyc" -delete
	@docker-compose exec backend find . -type d -name "__pycache__" -delete
	@docker-compose exec frontend npm run clean 2>/dev/null || true
	@echo "$(GREEN)Cache cleanup complete!$(RESET)"

reset: ## Full reset (stop, clean, rebuild, start)
	@echo "$(BLUE)Performing full reset...$(RESET)"
	@$(MAKE) stop
	@$(MAKE) clean
	@$(MAKE) build
	@$(MAKE) start
	@echo "$(GREEN)Full reset complete!$(RESET)"

update-deps: ## Update all dependencies
	@echo "$(BLUE)Updating dependencies...$(RESET)"
	@docker-compose exec backend pip list --outdated
	@docker-compose exec frontend npm outdated
	@echo "$(YELLOW)Review outdated packages above and update manually$(RESET)"

docs: ## Open API documentation
	@echo "$(BLUE)Opening API documentation...$(RESET)"
	@open http://localhost:8000/docs || xdg-open http://localhost:8000/docs || echo "Visit http://localhost:8000/docs"

# ==========================================
# Production Commands
# ==========================================

build-prod: ## Build production images
	@echo "$(BLUE)Building production images...$(RESET)"
	@docker-compose -f docker-compose.prod.yml build

deploy-prod: ## Deploy to production
	@echo "$(RED)Production deployment not implemented yet$(RESET)"
	@echo "This command will be added when production configuration is ready"

# ==========================================
# Development Tools
# ==========================================

monitor: ## Show resource monitoring
	@echo "$(BLUE)Resource monitoring:$(RESET)"
	@docker stats --no-stream

ports: ## Show port usage
	@echo "$(BLUE)Port usage:$(RESET)"
	@echo "3000: Frontend (Next.js)"
	@echo "8000: Backend (FastAPI)"
	@echo "6379: Redis"
	@echo "5432: PostgreSQL"
	@echo "9090: Prometheus (with --profile monitoring)"
	@echo "3001: Grafana (with --profile monitoring)"

env-check: ## Check environment configuration
	@echo "$(BLUE)Environment check:$(RESET)"
	@test -f .env.local && echo "$(GREEN)✓ .env.local exists$(RESET)" || echo "$(RED)✗ .env.local missing$(RESET)"
	@test -f backend/.env.local && echo "$(GREEN)✓ backend/.env.local exists$(RESET)" || echo "$(RED)✗ backend/.env.local missing$(RESET)"
	@test -f frontend/.env.local && echo "$(GREEN)✓ frontend/.env.local exists$(RESET)" || echo "$(RED)✗ frontend/.env.local missing$(RESET)"