# Makefile for Infra Mind development
# Learning Note: Makefiles provide convenient shortcuts for common development tasks

.PHONY: help install dev test clean docker-up docker-down docker-logs format lint type-check

# Default target
help:
	@echo "🚀 Infra Mind Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  install     Install dependencies"
	@echo "  dev         Install development dependencies"
	@echo ""
	@echo "Development:"
	@echo "  run         Run the application locally"
	@echo "  test        Run tests"
	@echo "  format      Format code with black and isort"
	@echo "  lint        Run linting with flake8"
	@echo "  type-check  Run type checking with mypy"
	@echo ""
	@echo "Docker:"
	@echo "  docker-up   Start all services with Docker Compose"
	@echo "  docker-down Stop all services"
	@echo "  docker-logs View logs from all services"
	@echo "  docker-build Build Docker images"
	@echo ""
	@echo "Utilities:"
	@echo "  clean       Clean up temporary files"
	@echo "  db-info     Show database information"
	@echo "  test-conn   Test database connections"

# Installation
install:
	pip install -e .

dev: install
	pip install -e ".[dev]"

# Development
run:
	python -m infra_mind.cli run --reload

test:
	pytest -v

format:
	black src/ tests/
	isort src/ tests/

lint:
	flake8 src/ tests/

type-check:
	mypy src/

# Docker commands
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-build:
	docker-compose build

docker-tools:
	docker-compose --profile tools up -d

# Database utilities
db-info:
	python -m infra_mind.cli db-info

test-conn:
	python -m infra_mind.cli test-connection

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +