#!/bin/bash

# Production Secrets Setup Script for Infra Mind
# This script helps set up secrets for different deployment environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="infra-mind"
SECRET_NAME="infra-mind-secrets"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Functions
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

# Check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check if we can connect to cluster
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log_success "kubectl is available and connected to cluster"
}

# Check if Docker is available
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    log_success "Docker is available"
}

# Create namespace if it doesn't exist
create_namespace() {
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_info "Namespace $NAMESPACE already exists"
    else
        kubectl create namespace "$NAMESPACE"
        log_success "Created namespace $NAMESPACE"
    fi
}

# Generate secure secret key
generate_secret_key() {
    python3 -c "import secrets; print(secrets.token_urlsafe(32))"
}

# Base64 encode a value
base64_encode() {
    echo -n "$1" | base64 | tr -d '\n'
}

# Setup environment file secrets
setup_env_secrets() {
    log_info "Setting up environment file secrets..."
    
    local env_file="$PROJECT_ROOT/.env.production"
    
    if [[ ! -f "$env_file" ]]; then
        log_error "Production environment file not found: $env_file"
        log_info "Please copy .env.production template and configure it"
        exit 1
    fi
    
    # Source the environment file
    set -a
    source "$env_file"
    set +a
    
    log_success "Loaded environment variables from $env_file"
}

# Setup Docker secrets
setup_docker_secrets() {
    log_info "Setting up Docker secrets..."
    
    # Check if running in Docker Swarm mode
    if ! docker info --format '{{.Swarm.LocalNodeState}}' | grep -q active; then
        log_warning "Docker Swarm is not active. Initializing..."
        docker swarm init
    fi
    
    # Create Docker secrets
    local secrets=(
        "infra_mind_mongodb_url:${INFRA_MIND_MONGODB_URL}"
        "infra_mind_redis_url:${INFRA_MIND_REDIS_URL}"
        "infra_mind_openai_api_key:${INFRA_MIND_OPENAI_API_KEY}"
        "infra_mind_aws_access_key_id:${INFRA_MIND_AWS_ACCESS_KEY_ID}"
        "infra_mind_aws_secret_access_key:${INFRA_MIND_AWS_SECRET_ACCESS_KEY}"
        "infra_mind_azure_client_id:${INFRA_MIND_AZURE_CLIENT_ID}"
        "infra_mind_azure_client_secret:${INFRA_MIND_AZURE_CLIENT_SECRET}"
        "infra_mind_azure_tenant_id:${INFRA_MIND_AZURE_TENANT_ID}"
        "infra_mind_gcp_service_account_json:${INFRA_MIND_GCP_SERVICE_ACCOUNT_JSON}"
        "infra_mind_jwt_secret_key:${INFRA_MIND_SECRET_KEY}"
    )
    
    for secret_def in "${secrets[@]}"; do
        IFS=':' read -r secret_name secret_value <<< "$secret_def"
        
        if [[ -n "$secret_value" ]]; then
            # Remove existing secret if it exists
            docker secret rm "$secret_name" 2>/dev/null || true
            
            # Create new secret
            echo -n "$secret_value" | docker secret create "$secret_name" -
            log_success "Created Docker secret: $secret_name"
        else
            log_warning "Skipping empty secret: $secret_name"
        fi
    done
}

# Setup Kubernetes secrets
setup_k8s_secrets() {
    log_info "Setting up Kubernetes secrets..."
    
    create_namespace
    
    # Remove existing secret if it exists
    kubectl delete secret "$SECRET_NAME" -n "$NAMESPACE" 2>/dev/null || true
    
    # Prepare secret data
    local secret_data=""
    
    # Add secrets if they exist
    if [[ -n "${INFRA_MIND_SECRET_KEY}" ]]; then
        secret_data+=" --from-literal=secret-key=${INFRA_MIND_SECRET_KEY}"
    fi
    
    if [[ -n "${INFRA_MIND_MONGODB_URL}" ]]; then
        secret_data+=" --from-literal=mongodb-url=${INFRA_MIND_MONGODB_URL}"
    fi
    
    if [[ -n "${INFRA_MIND_REDIS_URL}" ]]; then
        secret_data+=" --from-literal=redis-url=${INFRA_MIND_REDIS_URL}"
    fi
    
    if [[ -n "${INFRA_MIND_OPENAI_API_KEY}" ]]; then
        secret_data+=" --from-literal=openai-api-key=${INFRA_MIND_OPENAI_API_KEY}"
    fi
    
    if [[ -n "${INFRA_MIND_ANTHROPIC_API_KEY}" ]]; then
        secret_data+=" --from-literal=anthropic-api-key=${INFRA_MIND_ANTHROPIC_API_KEY}"
    fi
    
    if [[ -n "${INFRA_MIND_AWS_ACCESS_KEY_ID}" ]]; then
        secret_data+=" --from-literal=aws-access-key-id=${INFRA_MIND_AWS_ACCESS_KEY_ID}"
    fi
    
    if [[ -n "${INFRA_MIND_AWS_SECRET_ACCESS_KEY}" ]]; then
        secret_data+=" --from-literal=aws-secret-access-key=${INFRA_MIND_AWS_SECRET_ACCESS_KEY}"
    fi
    
    if [[ -n "${INFRA_MIND_AZURE_CLIENT_ID}" ]]; then
        secret_data+=" --from-literal=azure-client-id=${INFRA_MIND_AZURE_CLIENT_ID}"
    fi
    
    if [[ -n "${INFRA_MIND_AZURE_CLIENT_SECRET}" ]]; then
        secret_data+=" --from-literal=azure-client-secret=${INFRA_MIND_AZURE_CLIENT_SECRET}"
    fi
    
    if [[ -n "${INFRA_MIND_AZURE_TENANT_ID}" ]]; then
        secret_data+=" --from-literal=azure-tenant-id=${INFRA_MIND_AZURE_TENANT_ID}"
    fi
    
    if [[ -n "${INFRA_MIND_GCP_PROJECT_ID}" ]]; then
        secret_data+=" --from-literal=gcp-project-id=${INFRA_MIND_GCP_PROJECT_ID}"
    fi
    
    if [[ -n "${INFRA_MIND_GCP_SERVICE_ACCOUNT_JSON}" ]]; then
        secret_data+=" --from-literal=gcp-service-account-json=${INFRA_MIND_GCP_SERVICE_ACCOUNT_JSON}"
    fi
    
    if [[ -n "${INFRA_MIND_TF_CLOUD_TOKEN}" ]]; then
        secret_data+=" --from-literal=tf-cloud-token=${INFRA_MIND_TF_CLOUD_TOKEN}"
    fi
    
    if [[ -n "${INFRA_MIND_SENTRY_DSN}" ]]; then
        secret_data+=" --from-literal=sentry-dsn=${INFRA_MIND_SENTRY_DSN}"
    fi
    
    # Create the secret
    if [[ -n "$secret_data" ]]; then
        eval "kubectl create secret generic $SECRET_NAME -n $NAMESPACE $secret_data"
        log_success "Created Kubernetes secret: $SECRET_NAME"
    else
        log_error "No secret data found to create Kubernetes secret"
        exit 1
    fi
    
    # Apply ConfigMap
    kubectl apply -f "$PROJECT_ROOT/k8s/secrets.yaml" -n "$NAMESPACE"
    log_success "Applied Kubernetes ConfigMap"
}

# Validate secrets
validate_secrets() {
    log_info "Validating secrets configuration..."
    
    # Run the configuration validation script
    python3 "$SCRIPT_DIR/validate-config.py"
}

# Generate secrets template
generate_template() {
    log_info "Generating secrets template..."
    
    local template_file="$PROJECT_ROOT/.env.secrets.template"
    
    cat > "$template_file" << EOF
# Secrets Template for Infra Mind Production Deployment
# Copy this file to .env.production and fill in the actual values

# Application Security
INFRA_MIND_SECRET_KEY=$(generate_secret_key)

# Database URLs
INFRA_MIND_MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/infra_mind
INFRA_MIND_REDIS_URL=rediss://username:password@redis-cluster:6380

# LLM API Keys
INFRA_MIND_OPENAI_API_KEY=sk-your-openai-api-key-here
INFRA_MIND_ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here

# AWS Credentials
INFRA_MIND_AWS_ACCESS_KEY_ID=AKIA...
INFRA_MIND_AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key

# Azure Credentials
INFRA_MIND_AZURE_CLIENT_ID=your-azure-client-id
INFRA_MIND_AZURE_CLIENT_SECRET=your-azure-client-secret
INFRA_MIND_AZURE_TENANT_ID=your-azure-tenant-id
INFRA_MIND_AZURE_SUBSCRIPTION_ID=your-azure-subscription-id

# GCP Credentials
INFRA_MIND_GCP_PROJECT_ID=your-gcp-project-id
INFRA_MIND_GCP_SERVICE_ACCOUNT_JSON='{"type": "service_account", ...}'

# Terraform Cloud
INFRA_MIND_TF_CLOUD_TOKEN=your-terraform-cloud-token

# External Services
INFRA_MIND_GOOGLE_SEARCH_API_KEY=your-google-search-api-key
INFRA_MIND_BING_SEARCH_API_KEY=your-bing-search-api-key

# Monitoring
INFRA_MIND_SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
EOF
    
    log_success "Generated secrets template: $template_file"
    log_info "Please copy this file to .env.production and fill in the actual values"
}

# Show usage
show_usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  template    Generate secrets template file"
    echo "  docker      Setup Docker secrets"
    echo "  k8s         Setup Kubernetes secrets"
    echo "  validate    Validate secrets configuration"
    echo "  all         Setup secrets for all environments"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 template                 # Generate secrets template"
    echo "  $0 k8s                      # Setup Kubernetes secrets"
    echo "  $0 validate                 # Validate configuration"
}

# Main function
main() {
    local command="${1:-help}"
    
    case "$command" in
        template)
            generate_template
            ;;
        docker)
            check_docker
            setup_env_secrets
            setup_docker_secrets
            ;;
        k8s)
            check_kubectl
            setup_env_secrets
            setup_k8s_secrets
            ;;
        validate)
            setup_env_secrets
            validate_secrets
            ;;
        all)
            check_docker
            check_kubectl
            setup_env_secrets
            setup_docker_secrets
            setup_k8s_secrets
            validate_secrets
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            log_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"