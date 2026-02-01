# Makefile for AI-Driven Agri-Civic Intelligence Platform

.PHONY: help install setup dev test lint format clean docker-up docker-down validate

# Default target
help:
	@echo "AI-Driven Agri-Civic Intelligence Platform - Development Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  install     - Install dependencies with Poetry"
	@echo "  setup       - Setup development environment"
	@echo "  dev         - Run development server"
	@echo "  test        - Run tests"
	@echo "  lint        - Run linting checks"
	@echo "  format      - Format code with black and isort"
	@echo "  clean       - Clean up temporary files"
	@echo "  docker-up   - Start Docker services"
	@echo "  docker-down - Stop Docker services"
	@echo "  validate    - Validate project setup"

# Install dependencies
install:
	poetry install

# Setup development environment
setup:
	@echo "Setting up development environment..."
	@if [ ! -f .env ]; then cp .env.template .env; echo "Created .env file from template"; fi
	poetry install
	mkdir -p logs data uploads
	@echo "Setup complete! Please configure .env file with your API keys."

# Run development server
dev:
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
test:
	poetry run pytest tests/ -v --cov=app --cov-report=html --cov-report=term

# Run linting
lint:
	poetry run flake8 app tests
	poetry run mypy app

# Format code
format:
	poetry run black app tests
	poetry run isort app tests

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/

# Docker commands
docker-up:
	docker-compose up -d postgres redis

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# Validate setup
validate:
	python validate_setup.py

# Database commands (for future use)
db-upgrade:
	poetry run alembic upgrade head

db-downgrade:
	poetry run alembic downgrade -1

db-revision:
	poetry run alembic revision --autogenerate -m "$(message)"

# Production build
build:
	docker build -t agri-platform:latest .

# Security check
security:
	poetry run safety check
	poetry run bandit -r app/