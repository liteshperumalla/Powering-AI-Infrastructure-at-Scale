# Infra Mind - Production Deployment Makefile
# This Makefile provides convenient commands for building, testing, and deploying Infra Mind

.PHONY: help build test deploy clean security-scan performance-test

# Default target
.DEFAULT_GOAL := help

# Variables
REGISTRY ?= ghcr.io
REPO_NAME ?= infra-mind
IMAGE_TAG ?= latest
ENVIRONMENT ?= staging
NAMESPACE ?= infra-mind-staging

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Help target
help: ## Show this help message
	@echo "$(BLUE)Infra Mind - Production Deployment Commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Available targets:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)Environment Variables:$(NC)"
	@echo "  REGISTRY     Container registry (default: ghcr.io)"
	@echo "  REPO_NAME    Repository name (default: infra-mind)"
	@echo "  IMAGE_TAG    Image tag (default: latest)"
	@echo "  ENVIRONMENT  Deployment environment (default: staging)"
	@echo ""
	@echo "$(YELLOW)Examples:$(NC)"
	@echo "  make build IMAGE_TAG=v1.0.0"
	@echo "  make deploy ENVIRONMENT=production"
	@echo "  make test"

# Development targets
install: ## Install development dependencies
	@echo "$(BLUE)Installing Python dependencies...$(NC)"
	pip install -e .
	pip install pytest pytest-cov pytest-asyncio black flake8 mypy
	@echo "$(BLUE)Installing Node.js dependencies...$(NC)"
	cd frontend-react && npm install
	@echo "$(GREEN)Dependencies installed successfully!$(NC)"

format: ## Format code with Black and Prettier
	@echo "$(BLUE)Formatting Python code...$(NC)"
	black src/ tests/
	@echo "$(BLUE)Formatting TypeScript code...$(NC)"
	cd frontend-react && npm run format
	@echo "$(GREEN)Code formatting completed!$(NC)"

lint: ## Run linting checks
	@echo "$(BLUE)Running Python linting...$(NC)"
	flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203,W503
	mypy src/ --ignore-missing-imports
	@echo "$(BLUE)Running TypeScript linting...$(NC)"
	cd frontend-react && npm run lint
	@echo "$(GREEN)Linting completed!$(NC)"

test: ## Run all tests
	@echo "$(BLUE)Running Python tests...$(NC)"
	pytest tests/ -v --cov=src --cov-report=term-missing
	@echo "$(BLUE)Running Frontend tests...$(NC)"
	cd frontend-react && npm test -- --coverage --watchAll=false
	@echo "$(GREEN)All tests completed!$(NC)"

test-integration: ## Run integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
	docker-compose -f docker-compose.test.yml down
	@echo "$(GREEN)Integration tests completed!$(NC)"

# Build targets
build: ## Build Docker images
	@echo "$(BLUE)Building API image...$(NC)"
	docker build -t $(REGISTRY)/$(REPO_NAME)/api:$(IMAGE_TAG) .
	@echo "$(BLUE)Building Frontend image...$(NC)"
	docker build -t $(REGISTRY)/$(REPO_NAME)/frontend:$(IMAGE_TAG) ./frontend-react
	@echo "$(GREEN)Images built successfully!$(NC)"

build-push: build ## Build and push Docker images
	@echo "$(BLUE)Pushing API image...$(NC)"
	docker push $(REGISTRY)/$(REPO_NAME)/api:$(IMAGE_TAG)
	@echo "$(BLUE)Pushing Frontend image...$(NC)"
	docker push $(REGISTRY)/$(REPO_NAME)/frontend:$(IMAGE_TAG)
	@echo "$(GREEN)Images pushed successfully!$(NC)"

# Local development targets
dev-up: ## Start development environment
	@echo "$(BLUE)Starting development environment...$(NC)"
	docker-compose -f docker-compose.dev.yml up -d
	@echo "$(GREEN)Development environment started!$(NC)"
	@echo "Frontend: http://localhost:3000"
	@echo "API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"

dev-down: ## Stop development environment
	@echo "$(BLUE)Stopping development environment...$(NC)"
	docker-compose -f docker-compose.dev.yml down
	@echo "$(GREEN)Development environment stopped!$(NC)"

dev-logs: ## Show development environment logs
	docker-compose -f docker-compose.dev.yml logs -f

dev-restart: dev-down dev-up ## Restart development environment

# Production deployment targets
deploy-staging: ## Deploy to staging environment
	@echo "$(BLUE)Deploying to staging environment...$(NC)"
	./scripts/deploy-k8s.sh staging deploy
	@echo "$(GREEN)Staging deployment completed!$(NC)"

deploy-production: ## Deploy to production environment
	@echo "$(BLUE)Deploying to production environment...$(NC)"
	./scripts/deploy-k8s.sh production deploy
	@echo "$(GREEN)Production deployment completed!$(NC)"

deploy-update: ## Update existing deployment
	@echo "$(BLUE)Updating $(ENVIRONMENT) deployment...$(NC)"
	./scripts/deploy-k8s.sh $(ENVIRONMENT) update
	@echo "$(GREEN)Deployment updated!$(NC)"

deploy-rollback: ## Rollback deployment
	@echo "$(YELLOW)Rolling back $(ENVIRONMENT) deployment...$(NC)"
	./scripts/deploy-k8s.sh $(ENVIRONMENT) rollback
	@echo "$(GREEN)Rollback completed!$(NC)"

deploy-status: ## Show deployment status
	@echo "$(BLUE)Deployment status for $(ENVIRONMENT):$(NC)"
	./scripts/deploy-k8s.sh $(ENVIRONMENT) status

deploy-destroy: ## Destroy deployment (use with caution)
	@echo "$(RED)WARNING: This will destroy the $(ENVIRONMENT) deployment!$(NC)"
	./scripts/deploy-k8s.sh $(ENVIRONMENT) destroy

# Kubernetes management targets
k8s-apply: ## Apply Kubernetes manifests
	@echo "$(BLUE)Applying Kubernetes manifests...$(NC)"
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/configmap.yaml
	kubectl apply -f k8s/secrets.yaml
	kubectl apply -f k8s/mongodb-deployment.yaml
	kubectl apply -f k8s/redis-deployment.yaml
	kubectl apply -f k8s/api-deployment.yaml
	kubectl apply -f k8s/frontend-deployment.yaml
	kubectl apply -f k8s/ingress.yaml
	kubectl apply -f k8s/hpa.yaml
	@echo "$(GREEN)Kubernetes manifests applied!$(NC)"

k8s-delete: ## Delete Kubernetes resources
	@echo "$(YELLOW)Deleting Kubernetes resources...$(NC)"
	kubectl delete -f k8s/ --ignore-not-found=true
	@echo "$(GREEN)Kubernetes resources deleted!$(NC)"

k8s-logs: ## Show application logs
	@echo "$(BLUE)API logs:$(NC)"
	kubectl logs -l app=infra-mind-api -n $(NAMESPACE) --tail=50
	@echo "$(BLUE)Frontend logs:$(NC)"
	kubectl logs -l app=infra-mind-frontend -n $(NAMESPACE) --tail=50

k8s-shell: ## Get shell access to API pod
	kubectl exec -it deployment/infra-mind-api -n $(NAMESPACE) -- /bin/bash

k8s-port-forward: ## Port forward to local machine
	@echo "$(BLUE)Port forwarding API to localhost:8000...$(NC)"
	kubectl port-forward service/infra-mind-api-service 8000:8000 -n $(NAMESPACE) &
	@echo "$(BLUE)Port forwarding Frontend to localhost:3000...$(NC)"
	kubectl port-forward service/infra-mind-frontend-service 3000:3000 -n $(NAMESPACE) &
	@echo "$(GREEN)Port forwarding active. Press Ctrl+C to stop.$(NC)"

# Security targets
security-scan: ## Run security scans
	@echo "$(BLUE)Running security scans...$(NC)"
	@echo "$(BLUE)Scanning Python dependencies...$(NC)"
	pip install safety
	safety check
	@echo "$(BLUE)Scanning container images...$(NC)"
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy image $(REGISTRY)/$(REPO_NAME)/api:$(IMAGE_TAG)
	@echo "$(GREEN)Security scans completed!$(NC)"

security-audit: ## Run comprehensive security audit
	@echo "$(BLUE)Running comprehensive security audit...$(NC)"
	pip install bandit
	bandit -r src/ -f json -o bandit-report.json
	@echo "$(GREEN)Security audit completed! Check bandit-report.json$(NC)"

# Performance targets
performance-test: ## Run performance tests
	@echo "$(BLUE)Running performance tests...$(NC)"
	pip install locust
	locust -f tests/performance/locustfile.py --host=http://localhost:8000 \
		--users=10 --spawn-rate=2 --run-time=60s --headless
	@echo "$(GREEN)Performance tests completed!$(NC)"

load-test: ## Run load tests against staging
	@echo "$(BLUE)Running load tests against staging...$(NC)"
	pip install locust
	locust -f tests/performance/locustfile.py --host=https://api-staging.infra-mind.example.com \
		--users=50 --spawn-rate=5 --run-time=300s --headless
	@echo "$(GREEN)Load tests completed!$(NC)"

# Database targets
db-backup: ## Create database backup
	@echo "$(BLUE)Creating database backup...$(NC)"
	kubectl exec deployment/mongodb -n $(NAMESPACE) -- mongodump --out /tmp/backup
	kubectl cp $(NAMESPACE)/mongodb-pod:/tmp/backup ./backup-$(shell date +%Y%m%d-%H%M%S)
	@echo "$(GREEN)Database backup created!$(NC)"

db-restore: ## Restore database from backup
	@echo "$(BLUE)Restoring database from backup...$(NC)"
	@read -p "Enter backup directory name: " backup_dir; \
	kubectl cp ./$$backup_dir $(NAMESPACE)/mongodb-pod:/tmp/restore && \
	kubectl exec deployment/mongodb -n $(NAMESPACE) -- mongorestore /tmp/restore
	@echo "$(GREEN)Database restored!$(NC)"

db-shell: ## Connect to database shell
	kubectl exec -it deployment/mongodb -n $(NAMESPACE) -- mongosh

# Monitoring targets
monitoring-install: ## Install monitoring stack
	@echo "$(BLUE)Installing Prometheus and Grafana...$(NC)"
	helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
	helm repo update
	helm install prometheus prometheus-community/kube-prometheus-stack \
		--namespace monitoring --create-namespace
	@echo "$(GREEN)Monitoring stack installed!$(NC)"

monitoring-dashboard: ## Open Grafana dashboard
	@echo "$(BLUE)Opening Grafana dashboard...$(NC)"
	kubectl port-forward service/prometheus-grafana 3000:80 -n monitoring &
	@echo "$(GREEN)Grafana available at http://localhost:3000 (admin/prom-operator)$(NC)"

# Cleanup targets
clean: ## Clean up local resources
	@echo "$(BLUE)Cleaning up local resources...$(NC)"
	docker system prune -f
	docker volume prune -f
	@echo "$(GREEN)Cleanup completed!$(NC)"

clean-images: ## Remove local Docker images
	@echo "$(BLUE)Removing local Docker images...$(NC)"
	docker rmi $(REGISTRY)/$(REPO_NAME)/api:$(IMAGE_TAG) || true
	docker rmi $(REGISTRY)/$(REPO_NAME)/frontend:$(IMAGE_TAG) || true
	@echo "$(GREEN)Images removed!$(NC)"

# CI/CD targets
ci-test: ## Run CI tests (used by GitHub Actions)
	@echo "$(BLUE)Running CI tests...$(NC)"
	black --check --diff src/ tests/
	flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203,W503
	mypy src/ --ignore-missing-imports
	pytest tests/ -v --cov=src --cov-report=xml
	cd frontend-react && npm run lint && npm run type-check && npm test -- --coverage --watchAll=false
	@echo "$(GREEN)CI tests completed!$(NC)"

ci-build: ## Build images for CI
	@echo "$(BLUE)Building images for CI...$(NC)"
	docker build -t $(REGISTRY)/$(REPO_NAME)/api:$(GITHUB_SHA) .
	docker build -t $(REGISTRY)/$(REPO_NAME)/frontend:$(GITHUB_SHA) ./frontend-react
	@echo "$(GREEN)CI build completed!$(NC)"

# Documentation targets
docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation...$(NC)"
	python -m http.server 8080 -d docs/
	@echo "$(GREEN)Documentation available at http://localhost:8080$(NC)"

docs-build: ## Build documentation
	@echo "$(BLUE)Building documentation...$(NC)"
	# Add documentation build commands here
	@echo "$(GREEN)Documentation built!$(NC)"

# Utility targets
check-deps: ## Check for outdated dependencies
	@echo "$(BLUE)Checking Python dependencies...$(NC)"
	pip list --outdated
	@echo "$(BLUE)Checking Node.js dependencies...$(NC)"
	cd frontend-react && npm outdated
	@echo "$(GREEN)Dependency check completed!$(NC)"

update-deps: ## Update dependencies
	@echo "$(BLUE)Updating Python dependencies...$(NC)"
	pip install --upgrade pip
	pip install --upgrade -r requirements.txt
	@echo "$(BLUE)Updating Node.js dependencies...$(NC)"
	cd frontend-react && npm update
	@echo "$(GREEN)Dependencies updated!$(NC)"

version: ## Show version information
	@echo "$(BLUE)Version Information:$(NC)"
	@echo "Docker: $(shell docker --version)"
	@echo "kubectl: $(shell kubectl version --client --short 2>/dev/null || echo 'Not installed')"
	@echo "Helm: $(shell helm version --short 2>/dev/null || echo 'Not installed')"
	@echo "Python: $(shell python --version)"
	@echo "Node.js: $(shell node --version 2>/dev/null || echo 'Not installed')"
	@echo "npm: $(shell npm --version 2>/dev/null || echo 'Not installed')"