# ConcordBroker Makefile

.PHONY: help build up down logs clean test deploy

help:
	@echo "Available commands:"
	@echo "  make build    - Build all Docker images"
	@echo "  make up       - Start all services"
	@echo "  make down     - Stop all services"
	@echo "  make logs     - View logs from all services"
	@echo "  make clean    - Remove containers and volumes"
	@echo "  make test     - Run tests"
	@echo "  make deploy   - Deploy to production"

# Development commands
build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	docker system prune -f

# Service-specific commands
api:
	docker-compose up -d api

web:
	docker-compose up -d web

workers:
	docker-compose up -d sunbiz-worker bcpa-worker records-worker

# Database commands
db-migrate:
	docker-compose exec api alembic upgrade head

db-reset:
	docker-compose exec postgres psql -U concordbroker -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	make db-migrate

# Testing
test-api:
	docker-compose exec api pytest tests/

test-frontend:
	docker-compose exec web npm test

test: test-api test-frontend

# Production deployment
deploy-railway:
	railway up

deploy-vercel:
	cd apps/web && vercel --prod

deploy: deploy-railway deploy-vercel

# DOR processing (when data received)
process-dor:
	docker-compose --profile dor up -d dor-worker

# Monitoring
health-check:
	@echo "Checking API health..."
	@curl -f http://localhost:8000/health || echo "API is down"
	@echo "\nChecking Web health..."
	@curl -f http://localhost:5173 || echo "Web is down"

# Development setup
dev-setup:
	cp .env.example .env
	make build
	make up
	make db-migrate
	@echo "Development environment ready!"
	@echo "API: http://localhost:8000"
	@echo "Web: http://localhost:5173"