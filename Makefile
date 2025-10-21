# Backoffice Makefile

.PHONY: help install dev-install test lint format clean docker-up docker-down docker-logs migrate upgrade downgrade

# Default target
help:
	@echo "Available commands:"
	@echo "  install        - Install production dependencies"
	@echo "  dev-install    - Install development dependencies"
	@echo "  test           - Run tests"
	@echo "  lint           - Run linters"
	@echo "  format         - Format code"
	@echo "  clean          - Clean cache and temporary files"
	@echo "  docker-up      - Start Docker services"
	@echo "  docker-down    - Stop Docker services"
	@echo "  docker-logs    - Show Docker logs"
	@echo "  migrate        - Create new migration"
	@echo "  upgrade        - Apply migrations"
	@echo "  downgrade      - Rollback last migration"
	@echo "  s3-status      - Check S3/MinIO status"
	@echo "  s3-console     - Open MinIO console"

# Dependencies
install:
	poetry install --no-dev

dev-install:
	poetry install

# Testing
test:
	poetry run pytest tests/ -v

# Code quality
lint:
	poetry run black --check src/ tests/
	poetry run isort --check-only src/ tests/

format:
	poetry run black src/ tests/
	poetry run isort src/ tests/

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/

# Docker
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# Database migrations
migrate:
	poetry run alembic revision --autogenerate -m "$(MSG)"

upgrade:
	poetry run alembic upgrade head

downgrade:
	poetry run alembic downgrade -1

# S3/MinIO management
s3-status:
	@echo "Checking MinIO status..."
	@curl -s http://localhost:9000/minio/health/live && echo "MinIO is running" || echo "MinIO is not accessible"
	@echo "MinIO Console: http://localhost:9001"
	@echo "MinIO API: http://localhost:9000"

s3-console:
	@echo "Opening MinIO console..."
	@open http://localhost:9001 || xdg-open http://localhost:9001 || echo "Please open http://localhost:9001 manually"

# Development setup
setup-dev: dev-install docker-up
	@echo "Waiting for services to start..."
	@sleep 10
	@echo "Applying migrations..."
	@make upgrade
	@echo "Development environment ready!"
	@echo "MinIO Console: http://localhost:9001"
	@echo "API Documentation: http://localhost:8000/docs"

# Production setup
setup-prod: install docker-up
	@echo "Waiting for services to start..."
	@sleep 10
	@echo "Applying migrations..."
	@make upgrade
	@echo "Production environment ready!"

# Quick start
start: docker-up
	@echo "Services started. Check status with 'make s3-status'"

stop: docker-down
	@echo "Services stopped"
