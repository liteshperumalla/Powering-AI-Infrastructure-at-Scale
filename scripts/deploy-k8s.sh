#!/bin/bash

# Kubernetes Deployment Script for Infra Mind
# Usage: ./scripts/deploy-k8s.sh [environment] [action]
# Environment: staging, production
# Action: deploy, update, rollback, destroy

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
K8S_DIR="$PROJECT_ROOT/k8s"

# Default values
ENVIRONMENT="${1:-staging}"
ACTION="${2:-deploy}"
NAMESPACE="infra-mind"
REGISTRY="ghcr.io"
IMAGE_TAG="${GITHUB_SHA:-latest}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validation functions
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    # Check if helm is installed (optional)
    if ! command -v helm &> /dev/null; then
        log_warning "helm is not installed. Some features may not be available."
    fi
    
    # Check kubectl connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    
    # Check if namespace exists for production
    if [[ "$ENVIRONMENT" == "production" ]]; then
        NAMESPACE="infra-mind"
    else
        NAMESPACE="infra-mind-staging"
    fi
    
    log_success "Prerequisites check completed"
}

# Environment setup
setup_environment() {
    log_info "Setting up environment: $ENVIRONMENT"
    
    # Set environment-specific variables
    case $ENVIRONMENT in
        "staging")
            NAMESPACE="infra-mind-staging"
            REPLICAS_API=2
            REPLICAS_FRONTEND=1
            STORAGE_CLASS="standard"
            ;;
        "production")
            NAMESPACE="infra-mind"
            REPLICAS_API=3
            REPLICAS_FRONTEND=2
            STORAGE_CLASS="fast-ssd"
            ;;
        *)
            log_error "Invalid environment: $ENVIRONMENT. Use 'staging' or 'production'"
            exit 1
            ;;
    esac
    
    log_info "Using namespace: $NAMESPACE"
    log_info "API replicas: $REPLICAS_API"
    log_info "Frontend replicas: $REPLICAS_FRONTEND"
}

# Create namespace if it doesn't exist
create_namespace() {
    log_info "Creating namespace if it doesn't exist..."
    
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        kubectl apply -f "$K8S_DIR/namespace.yaml"
        log_success "Namespace created: $NAMESPACE"
    else
        log_info "Namespace already exists: $NAMESPACE"
    fi
}

# Deploy secrets
deploy_secrets() {
    log_info "Deploying secrets..."
    
    # Check if secrets exist
    if kubectl get secret infra-mind-secrets -n "$NAMESPACE" &> /dev/null; then
        log_warning "Secrets already exist. Skipping secret creation."
        log_warning "To update secrets, delete them first: kubectl delete secret infra-mind-secrets -n $NAMESPACE"
    else
        # Apply secrets (make sure they are properly configured)
        kubectl apply -f "$K8S_DIR/secrets.yaml" -n "$NAMESPACE"
        log_success "Secrets deployed"
    fi
    
    # Deploy Vault integration if available
    if [[ -f "$K8S_DIR/vault-integration.yaml" ]]; then
        log_info "Deploying Vault integration..."
        kubectl apply -f "$K8S_DIR/vault-integration.yaml" -n "$NAMESPACE"
        log_success "Vault integration deployed"
    fi
}

# Deploy configuration
deploy_config() {
    log_info "Deploying configuration..."
    
    kubectl apply -f "$K8S_DIR/configmap.yaml"
    log_success "Configuration deployed"
}

# Deploy database
deploy_database() {
    log_info "Deploying database components..."
    
    # Deploy MongoDB
    kubectl apply -f "$K8S_DIR/mongodb-deployment.yaml" -n "$NAMESPACE"
    
    # Deploy Redis
    kubectl apply -f "$K8S_DIR/redis-deployment.yaml" -n "$NAMESPACE"
    
    # Wait for databases to be ready
    log_info "Waiting for databases to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/mongodb -n "$NAMESPACE"
    kubectl wait --for=condition=available --timeout=300s deployment/redis -n "$NAMESPACE"
    
    log_success "Database components deployed"
}

# Update image tags
update_image_tags() {
    log_info "Updating image tags to: $IMAGE_TAG"
    
    # Create temporary files with updated image tags
    cp "$K8S_DIR/api-deployment.yaml" "/tmp/api-deployment-$ENVIRONMENT.yaml"
    cp "$K8S_DIR/frontend-deployment.yaml" "/tmp/frontend-deployment-$ENVIRONMENT.yaml"
    
    # Update image tags
    sed -i "s|image: infra-mind/api:.*|image: $REGISTRY/infra-mind/api:$IMAGE_TAG|g" "/tmp/api-deployment-$ENVIRONMENT.yaml"
    sed -i "s|image: infra-mind/frontend:.*|image: $REGISTRY/infra-mind/frontend:$IMAGE_TAG|g" "/tmp/frontend-deployment-$ENVIRONMENT.yaml"
    
    # Update replicas for environment
    sed -i "s|replicas: [0-9]*|replicas: $REPLICAS_API|g" "/tmp/api-deployment-$ENVIRONMENT.yaml"
    sed -i "s|replicas: [0-9]*|replicas: $REPLICAS_FRONTEND|g" "/tmp/frontend-deployment-$ENVIRONMENT.yaml"
    
    log_success "Image tags updated"
}

# Deploy applications
deploy_applications() {
    log_info "Deploying applications..."
    
    # Deploy API
    kubectl apply -f "/tmp/api-deployment-$ENVIRONMENT.yaml" -n "$NAMESPACE"
    
    # Deploy Frontend
    kubectl apply -f "/tmp/frontend-deployment-$ENVIRONMENT.yaml" -n "$NAMESPACE"
    
    # Wait for applications to be ready
    log_info "Waiting for applications to be ready..."
    kubectl wait --for=condition=available --timeout=600s deployment/infra-mind-api -n "$NAMESPACE"
    kubectl wait --for=condition=available --timeout=600s deployment/infra-mind-frontend -n "$NAMESPACE"
    
    log_success "Applications deployed"
}

# Deploy ingress and networking
deploy_networking() {
    log_info "Deploying networking components..."
    
    kubectl apply -f "$K8S_DIR/ingress.yaml"
    
    # Deploy HPA for production
    if [[ "$ENVIRONMENT" == "production" ]]; then
        kubectl apply -f "$K8S_DIR/hpa.yaml" -n "$NAMESPACE"
        log_success "HPA deployed for production"
    fi
    
    log_success "Networking components deployed"
}

# Run health checks
run_health_checks() {
    log_info "Running health checks..."
    
    # Wait a bit for services to stabilize
    sleep 30
    
    # Check API health
    if kubectl run test-pod --image=curlimages/curl:latest --rm -i --restart=Never -n "$NAMESPACE" -- \
       curl -f http://infra-mind-api-service:8000/health; then
        log_success "API health check passed"
    else
        log_error "API health check failed"
        return 1
    fi
    
    # Check Frontend health
    if kubectl run test-pod --image=curlimages/curl:latest --rm -i --restart=Never -n "$NAMESPACE" -- \
       curl -f http://infra-mind-frontend-service:3000/health; then
        log_success "Frontend health check passed"
    else
        log_error "Frontend health check failed"
        return 1
    fi
    
    log_success "All health checks passed"
}

# Rollback deployment
rollback_deployment() {
    log_info "Rolling back deployment..."
    
    # Rollback API
    kubectl rollout undo deployment/infra-mind-api -n "$NAMESPACE"
    
    # Rollback Frontend
    kubectl rollout undo deployment/infra-mind-frontend -n "$NAMESPACE"
    
    # Wait for rollback to complete
    kubectl rollout status deployment/infra-mind-api -n "$NAMESPACE" --timeout=300s
    kubectl rollout status deployment/infra-mind-frontend -n "$NAMESPACE" --timeout=300s
    
    log_success "Rollback completed"
}

# Destroy deployment
destroy_deployment() {
    log_warning "Destroying deployment in namespace: $NAMESPACE"
    read -p "Are you sure you want to destroy the deployment? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Destroying deployment..."
        
        # Delete applications
        kubectl delete -f "$K8S_DIR/api-deployment.yaml" -n "$NAMESPACE" --ignore-not-found=true
        kubectl delete -f "$K8S_DIR/frontend-deployment.yaml" -n "$NAMESPACE" --ignore-not-found=true
        
        # Delete databases
        kubectl delete -f "$K8S_DIR/mongodb-deployment.yaml" -n "$NAMESPACE" --ignore-not-found=true
        kubectl delete -f "$K8S_DIR/redis-deployment.yaml" -n "$NAMESPACE" --ignore-not-found=true
        
        # Delete networking
        kubectl delete -f "$K8S_DIR/ingress.yaml" --ignore-not-found=true
        kubectl delete -f "$K8S_DIR/hpa.yaml" -n "$NAMESPACE" --ignore-not-found=true
        
        # Delete configuration (but keep secrets)
        kubectl delete -f "$K8S_DIR/configmap.yaml" --ignore-not-found=true
        
        log_success "Deployment destroyed"
    else
        log_info "Deployment destruction cancelled"
    fi
}

# Show deployment status
show_status() {
    log_info "Deployment status for namespace: $NAMESPACE"
    
    echo
    echo "=== Pods ==="
    kubectl get pods -n "$NAMESPACE"
    
    echo
    echo "=== Services ==="
    kubectl get services -n "$NAMESPACE"
    
    echo
    echo "=== Ingress ==="
    kubectl get ingress -n "$NAMESPACE"
    
    echo
    echo "=== PVCs ==="
    kubectl get pvc -n "$NAMESPACE"
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        echo
        echo "=== HPA ==="
        kubectl get hpa -n "$NAMESPACE"
    fi
}

# Main deployment function
deploy() {
    log_info "Starting deployment to $ENVIRONMENT environment"
    
    check_prerequisites
    setup_environment
    create_namespace
    deploy_config
    deploy_secrets
    deploy_database
    update_image_tags
    deploy_applications
    deploy_networking
    
    log_success "Deployment completed successfully!"
    
    # Run health checks
    if run_health_checks; then
        log_success "All systems are healthy!"
    else
        log_error "Health checks failed. Please investigate."
        exit 1
    fi
    
    # Show status
    show_status
    
    # Cleanup temporary files
    rm -f "/tmp/api-deployment-$ENVIRONMENT.yaml" "/tmp/frontend-deployment-$ENVIRONMENT.yaml"
}

# Main script logic
main() {
    case $ACTION in
        "deploy")
            deploy
            ;;
        "update")
            log_info "Updating deployment..."
            update_image_tags
            deploy_applications
            run_health_checks
            ;;
        "rollback")
            rollback_deployment
            ;;
        "destroy")
            destroy_deployment
            ;;
        "status")
            show_status
            ;;
        *)
            log_error "Invalid action: $ACTION"
            echo "Usage: $0 [environment] [action]"
            echo "Environment: staging, production"
            echo "Action: deploy, update, rollback, destroy, status"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"