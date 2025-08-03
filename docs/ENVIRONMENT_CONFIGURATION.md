# Environment Configuration Guide

## Overview

This guide provides comprehensive documentation for configuring the Infra Mind platform across different environments (development, staging, production). It covers all configuration aspects including environment variables, secrets management, database setup, and external service integrations.

## Table of Contents

1. [Environment Overview](#environment-overview)
2. [Environment Variables](#environment-variables)
3. [Secrets Management](#secrets-management)
4. [Database Configuration](#database-configuration)
5. [External Service Configuration](#external-service-configuration)
6. [Security Configuration](#security-configuration)
7. [Monitoring Configuration](#monitoring-configuration)
8. [Deployment Configuration](#deployment-configuration)
9. [Troubleshooting](#troubleshooting)

## Environment Overview

### Environment Types

#### Development Environment
- **Purpose**: Local development and testing
- **Database**: Local MongoDB and Redis instances
- **External APIs**: Sandbox/test endpoints where available
- **Security**: Relaxed for development convenience
- **Monitoring**: Basic logging and metrics

#### Staging Environment
- **Purpose**: Pre-production testing and validation
- **Database**: Staging MongoDB and Redis clusters
- **External APIs**: Test/sandbox environments
- **Security**: Production-like security measures
- **Monitoring**: Full monitoring stack

#### Production Environment
- **Purpose**: Live customer-facing system
- **Database**: Production MongoDB and Redis clusters
- **External APIs**: Live production APIs
- **Security**: Full enterprise security measures
- **Monitoring**: Comprehensive monitoring and alerting

### Configuration Hierarchy

```
Environment Configuration Priority (highest to lowest):
1. Kubernetes Secrets (production)
2. Environment Variables
3. .env files
4. Configuration files (YAML)
5. Default values in code
```

## Environment Variables

### Core Application Variables

#### Basic Configuration
```bash
# Environment identification
ENVIRONMENT=production|staging|development
DEBUG=false
LOG_LEVEL=INFO|DEBUG|WARNING|ERROR

# Application settings
APP_NAME=infra-mind
APP_VERSION=1.0.0
APP_HOST=0.0.0.0
APP_PORT=8000

# Security
SECRET_KEY=${SECRET_KEY}
JWT_SECRET_KEY=${JWT_SECRET_KEY}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# CORS settings
CORS_ORIGINS=https://app.infra-mind.com,https://staging.infra-mind.com
CORS_ALLOW_CREDENTIALS=true
```

#### Database Configuration
```bash
# MongoDB
MONGODB_URL=mongodb://username:password@host:port/database
MONGODB_DATABASE=infra_mind_prod
MONGODB_MIN_POOL_SIZE=10
MONGODB_MAX_POOL_SIZE=100
MONGODB_MAX_IDLE_TIME_MS=30000

# Redis
REDIS_URL=redis://username:password@host:port/db
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_DB=0
REDIS_MAX_CONNECTIONS=100
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5
```

### External Service Configuration

#### Cloud Provider APIs
```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
AWS_DEFAULT_REGION=us-east-1
AWS_SESSION_TOKEN=${AWS_SESSION_TOKEN}  # If using temporary credentials

# Azure Configuration
AZURE_CLIENT_ID=${AZURE_CLIENT_ID}
AZURE_CLIENT_SECRET=${AZURE_CLIENT_SECRET}
AZURE_TENANT_ID=${AZURE_TENANT_ID}
AZURE_SUBSCRIPTION_ID=${AZURE_SUBSCRIPTION_ID}

# Google Cloud Configuration
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
GCP_PROJECT_ID=${GCP_PROJECT_ID}
GCP_REGION=us-central1

# Terraform Cloud
TERRAFORM_CLOUD_TOKEN=${TERRAFORM_CLOUD_TOKEN}
TERRAFORM_ORGANIZATION=${TERRAFORM_ORGANIZATION}
```

#### LLM Provider Configuration
```bash
# OpenAI
OPENAI_API_KEY=${OPENAI_API_KEY}
OPENAI_ORGANIZATION=${OPENAI_ORGANIZATION}
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=4000
OPENAI_TEMPERATURE=0.7

# Anthropic
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
ANTHROPIC_MODEL=claude-3-opus-20240229
ANTHROPIC_MAX_TOKENS=4000

# Azure OpenAI (if using)
AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
AZURE_OPENAI_API_VERSION=2023-12-01-preview
```

#### Search and Research APIs
```bash
# Google Custom Search
GOOGLE_SEARCH_API_KEY=${GOOGLE_SEARCH_API_KEY}
GOOGLE_SEARCH_ENGINE_ID=${GOOGLE_SEARCH_ENGINE_ID}

# Bing Search
BING_SEARCH_API_KEY=${BING_SEARCH_API_KEY}
BING_SEARCH_ENDPOINT=https://api.bing.microsoft.com/v7.0/search

# Web scraping configuration
SCRAPY_USER_AGENT=InfraMind-Bot/1.0
SCRAPY_DOWNLOAD_DELAY=1
SCRAPY_CONCURRENT_REQUESTS=16
```

### Monitoring and Logging

```bash
# Logging
LOG_FORMAT=json
LOG_FILE=/var/log/infra-mind/app.log
LOG_MAX_SIZE=100MB
LOG_BACKUP_COUNT=5

# Metrics
PROMETHEUS_METRICS_ENABLED=true
PROMETHEUS_METRICS_PORT=9090
METRICS_NAMESPACE=infra_mind

# Tracing
JAEGER_AGENT_HOST=jaeger-agent
JAEGER_AGENT_PORT=6831
JAEGER_SAMPLER_TYPE=probabilistic
JAEGER_SAMPLER_PARAM=0.1

# Health checks
HEALTH_CHECK_INTERVAL=30
HEALTH_CHECK_TIMEOUT=10
```

### Performance and Scaling

```bash
# Worker configuration
WORKER_PROCESSES=4
WORKER_CONNECTIONS=1000
WORKER_TIMEOUT=30

# Cache configuration
CACHE_TTL_DEFAULT=3600
CACHE_TTL_PRICING=7200
CACHE_TTL_SERVICES=14400
CACHE_MAX_SIZE=1GB

# Rate limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_BURST=20

# Agent configuration
AGENT_TIMEOUT=300
AGENT_MAX_CONCURRENT=10
AGENT_RETRY_ATTEMPTS=3
```

## Secrets Management

### Kubernetes Secrets

#### Creating Secrets
```bash
# Create secret from literal values
kubectl create secret generic infra-mind-secrets \
  --from-literal=mongodb-password=<password> \
  --from-literal=redis-password=<password> \
  --from-literal=jwt-secret=<jwt-secret> \
  --from-literal=openai-api-key=<api-key> \
  -n infra-mind-prod

# Create secret from file
kubectl create secret generic infra-mind-gcp-key \
  --from-file=service-account-key.json=/path/to/key.json \
  -n infra-mind-prod

# Create TLS secret
kubectl create secret tls infra-mind-tls \
  --cert=/path/to/tls.crt \
  --key=/path/to/tls.key \
  -n infra-mind-prod
```

#### Secret Management Best Practices
```yaml
# Example secret manifest
apiVersion: v1
kind: Secret
metadata:
  name: infra-mind-secrets
  namespace: infra-mind-prod
type: Opaque
data:
  mongodb-password: <base64-encoded-password>
  redis-password: <base64-encoded-password>
  jwt-secret: <base64-encoded-secret>
  openai-api-key: <base64-encoded-key>
  aws-access-key-id: <base64-encoded-key>
  aws-secret-access-key: <base64-encoded-key>
```

### HashiCorp Vault Integration

#### Vault Configuration
```bash
# Vault server configuration
export VAULT_ADDR=https://vault.infra-mind.com
export VAULT_TOKEN=${VAULT_TOKEN}

# Store secrets in Vault
vault kv put secret/infra-mind/prod \
  mongodb-password=<password> \
  redis-password=<password> \
  jwt-secret=<secret> \
  openai-api-key=<key>

# Retrieve secrets from Vault
vault kv get -field=mongodb-password secret/infra-mind/prod
```

#### Vault Agent Configuration
```hcl
# vault-agent.hcl
vault {
  address = "https://vault.infra-mind.com"
}

auto_auth {
  method "kubernetes" {
    mount_path = "auth/kubernetes"
    config = {
      role = "infra-mind-role"
    }
  }
}

template {
  source      = "/etc/vault/templates/secrets.env.tpl"
  destination = "/etc/secrets/secrets.env"
  perms       = 0600
}
```

### Environment-Specific Secrets

#### Development Environment
```bash
# .env.development
MONGODB_URL=mongodb://localhost:27017/infra_mind_dev
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-test-key-for-development
AWS_ACCESS_KEY_ID=test-access-key
AWS_SECRET_ACCESS_KEY=test-secret-key
DEBUG=true
LOG_LEVEL=DEBUG
```

#### Staging Environment
```bash
# .env.staging
MONGODB_URL=mongodb://mongo-staging:27017/infra_mind_staging
REDIS_URL=redis://redis-staging:6379/0
OPENAI_API_KEY=${OPENAI_API_KEY_STAGING}
AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID_STAGING}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY_STAGING}
DEBUG=false
LOG_LEVEL=INFO
```

#### Production Environment
```bash
# Production secrets managed via Kubernetes secrets
# No .env file in production - all from secrets/environment
```

## Database Configuration

### MongoDB Configuration

#### Replica Set Configuration
```javascript
// MongoDB replica set initialization
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "mongodb-0.mongodb:27017", priority: 2 },
    { _id: 1, host: "mongodb-1.mongodb:27017", priority: 1 },
    { _id: 2, host: "mongodb-2.mongodb:27017", priority: 1 }
  ]
});

// Create application user
use infra_mind_prod;
db.createUser({
  user: "infra_mind_app",
  pwd: "<secure-password>",
  roles: [
    { role: "readWrite", db: "infra_mind_prod" },
    { role: "dbAdmin", db: "infra_mind_prod" }
  ]
});
```

#### MongoDB Configuration File
```yaml
# mongod.conf
storage:
  dbPath: /data/db
  journal:
    enabled: true
  wiredTiger:
    engineConfig:
      cacheSizeGB: 4
      journalCompressor: snappy
    collectionConfig:
      blockCompressor: snappy

systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log
  logRotate: reopen

net:
  port: 27017
  bindIp: 0.0.0.0

security:
  authorization: enabled
  keyFile: /etc/mongodb/keyfile

replication:
  replSetName: rs0

processManagement:
  fork: true
  pidFilePath: /var/run/mongodb/mongod.pid
```

#### Database Indexes
```javascript
// Create performance indexes
db.assessments.createIndex({ user_id: 1, created_at: -1 });
db.assessments.createIndex({ status: 1, updated_at: -1 });
db.reports.createIndex({ assessment_id: 1 });
db.reports.createIndex({ user_id: 1, created_at: -1 });
db.users.createIndex({ email: 1 }, { unique: true });
db.workflow_states.createIndex({ status: 1, updated_at: -1 });
db.agent_metrics.createIndex({ agent_type: 1, timestamp: -1 });
```

### Redis Configuration

#### Redis Cluster Configuration
```conf
# redis.conf
port 6379
cluster-enabled yes
cluster-config-file nodes.conf
cluster-node-timeout 5000
appendonly yes
appendfsync everysec

# Memory management
maxmemory 2gb
maxmemory-policy allkeys-lru

# Security
requirepass <redis-password>
masterauth <redis-password>

# Persistence
save 900 1
save 300 10
save 60 10000

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log
```

#### Redis Sentinel Configuration
```conf
# sentinel.conf
port 26379
sentinel monitor mymaster redis-master 6379 2
sentinel auth-pass mymaster <redis-password>
sentinel down-after-milliseconds mymaster 5000
sentinel parallel-syncs mymaster 1
sentinel failover-timeout mymaster 10000
```

## External Service Configuration

### Cloud Provider Setup

#### AWS Configuration
```bash
# AWS CLI configuration
aws configure set aws_access_key_id ${AWS_ACCESS_KEY_ID}
aws configure set aws_secret_access_key ${AWS_SECRET_ACCESS_KEY}
aws configure set default.region us-east-1
aws configure set default.output json

# IAM policy for Infra Mind service
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "pricing:GetProducts",
        "pricing:GetAttributeValues",
        "ec2:DescribeInstances",
        "ec2:DescribeInstanceTypes",
        "rds:DescribeDBInstances",
        "s3:ListBucket",
        "s3:GetObject"
      ],
      "Resource": "*"
    }
  ]
}
```

#### Azure Configuration
```bash
# Azure service principal creation
az ad sp create-for-rbac --name "infra-mind-sp" \
  --role "Reader" \
  --scopes "/subscriptions/${SUBSCRIPTION_ID}"

# Required permissions
az role assignment create \
  --assignee ${CLIENT_ID} \
  --role "Cost Management Reader" \
  --scope "/subscriptions/${SUBSCRIPTION_ID}"
```

#### GCP Configuration
```bash
# Create service account
gcloud iam service-accounts create infra-mind-sa \
  --display-name="Infra Mind Service Account"

# Grant necessary roles
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:infra-mind-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/compute.viewer"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:infra-mind-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/cloudsql.viewer"

# Create and download key
gcloud iam service-accounts keys create service-account-key.json \
  --iam-account=infra-mind-sa@${PROJECT_ID}.iam.gserviceaccount.com
```

### LLM Provider Setup

#### OpenAI Configuration
```python
# OpenAI client configuration
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")
openai.organization = os.getenv("OPENAI_ORGANIZATION")

# Rate limiting configuration
OPENAI_RATE_LIMITS = {
    "requests_per_minute": 3000,
    "tokens_per_minute": 250000,
    "requests_per_day": 200000
}
```

#### Anthropic Configuration
```python
# Anthropic client configuration
import anthropic

client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

# Rate limiting configuration
ANTHROPIC_RATE_LIMITS = {
    "requests_per_minute": 1000,
    "tokens_per_minute": 100000,
    "requests_per_day": 50000
}
```

## Security Configuration

### TLS/SSL Configuration

#### Certificate Management
```bash
# Let's Encrypt certificate generation
certbot certonly --nginx \
  -d api.infra-mind.com \
  -d app.infra-mind.com \
  --email admin@infra-mind.com \
  --agree-tos \
  --non-interactive

# Certificate renewal automation
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
```

#### NGINX SSL Configuration
```nginx
# nginx.conf SSL configuration
server {
    listen 443 ssl http2;
    server_name api.infra-mind.com;

    ssl_certificate /etc/letsencrypt/live/api.infra-mind.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.infra-mind.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
}
```

### Authentication Configuration

#### JWT Configuration
```python
# JWT settings
JWT_SETTINGS = {
    "algorithm": "HS256",
    "access_token_expire_minutes": 60,
    "refresh_token_expire_days": 30,
    "issuer": "infra-mind.com",
    "audience": "infra-mind-api"
}

# Password hashing
BCRYPT_SETTINGS = {
    "rounds": 12,
    "salt_rounds": 12
}
```

#### OAuth Configuration (if applicable)
```python
# OAuth providers configuration
OAUTH_PROVIDERS = {
    "google": {
        "client_id": os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
        "redirect_uri": "https://app.infra-mind.com/auth/google/callback"
    },
    "microsoft": {
        "client_id": os.getenv("MICROSOFT_OAUTH_CLIENT_ID"),
        "client_secret": os.getenv("MICROSOFT_OAUTH_CLIENT_SECRET"),
        "redirect_uri": "https://app.infra-mind.com/auth/microsoft/callback"
    }
}
```

### Network Security

#### Firewall Rules
```bash
# UFW firewall configuration
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow from 10.0.0.0/8 to any port 27017  # MongoDB
ufw allow from 10.0.0.0/8 to any port 6379   # Redis
ufw enable
```

#### Network Policies (Kubernetes)
```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: infra-mind-network-policy
  namespace: infra-mind-prod
spec:
  podSelector:
    matchLabels:
      app: infra-mind-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: mongodb
    ports:
    - protocol: TCP
      port: 27017
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
```

## Monitoring Configuration

### Prometheus Configuration

#### Prometheus Config
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "infra_mind_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'infra-mind-api'
    static_configs:
      - targets: ['api.infra-mind.com:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'mongodb'
    static_configs:
      - targets: ['mongodb-exporter:9216']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

#### Alert Rules
```yaml
# infra_mind_rules.yml
groups:
- name: infra_mind_alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: High error rate detected

  - alert: DatabaseConnectionFailure
    expr: mongodb_up == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: MongoDB connection failure

  - alert: HighMemoryUsage
    expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.85
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: High memory usage detected
```

### Grafana Configuration

#### Dashboard Configuration
```json
{
  "dashboard": {
    "title": "Infra Mind System Overview",
    "panels": [
      {
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])",
            "legendFormat": "5xx errors"
          }
        ]
      }
    ]
  }
}
```

### Logging Configuration

#### ELK Stack Configuration
```yaml
# logstash.conf
input {
  beats {
    port => 5044
  }
}

filter {
  if [fields][service] == "infra-mind-api" {
    json {
      source => "message"
    }
    
    date {
      match => [ "timestamp", "ISO8601" ]
    }
    
    mutate {
      add_field => { "service" => "infra-mind-api" }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "infra-mind-logs-%{+YYYY.MM.dd}"
  }
}
```

## Deployment Configuration

### Docker Configuration

#### Production Dockerfile
```dockerfile
# Dockerfile.prod
FROM python:3.11-slim

# Security updates
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY api/ ./api/

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start application
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Docker Compose for Development
```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
      - DEBUG=true
      - MONGODB_URL=mongodb://mongodb:27017/infra_mind_dev
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./src:/app/src
      - ./api:/app/api
    depends_on:
      - mongodb
      - redis

  mongodb:
    image: mongo:7.0
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

  redis:
    image: redis:7.0
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  mongodb_data:
  redis_data:
```

### Kubernetes Configuration

#### Production Deployment
```yaml
# k8s/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: infra-mind-api
  namespace: infra-mind-prod
spec:
  replicas: 3
  selector:
    matchLabels:
      app: infra-mind-api
  template:
    metadata:
      labels:
        app: infra-mind-api
    spec:
      containers:
      - name: api
        image: infra-mind-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: MONGODB_URL
          valueFrom:
            secretKeyRef:
              name: infra-mind-secrets
              key: mongodb-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: infra-mind-secrets
              key: redis-url
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: infra-mind-secrets
              key: openai-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

## Troubleshooting

### Common Configuration Issues

#### Environment Variable Problems
```bash
# Check environment variables
printenv | grep INFRA_MIND
env | sort

# Verify Kubernetes secrets
kubectl get secrets -n infra-mind-prod
kubectl describe secret infra-mind-secrets -n infra-mind-prod

# Test secret values
kubectl get secret infra-mind-secrets -n infra-mind-prod -o jsonpath='{.data.mongodb-url}' | base64 -d
```

#### Database Connection Issues
```bash
# Test MongoDB connection
mongo --eval "db.runCommand({ping: 1})" mongodb://username:password@host:port/database

# Test Redis connection
redis-cli -h host -p port -a password ping

# Check network connectivity
telnet mongodb-host 27017
telnet redis-host 6379
```

#### External API Issues
```bash
# Test AWS credentials
aws sts get-caller-identity

# Test Azure credentials
az account show

# Test GCP credentials
gcloud auth list
gcloud projects list

# Test OpenAI API
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
```

### Configuration Validation

#### Validation Scripts
```bash
# Validate all configurations
python scripts/validate-config.py --environment=production

# Test database connections
python scripts/test-db-connections.py

# Verify external API access
python scripts/test-external-apis.py

# Check security configuration
python scripts/security-audit.py
```

#### Health Checks
```bash
# Application health check
curl -f http://api.infra-mind.com/health

# Database health check
curl -f http://api.infra-mind.com/health/database

# External services health check
curl -f http://api.infra-mind.com/health/external
```

### Performance Tuning

#### Database Optimization
```javascript
// MongoDB performance tuning
db.adminCommand({setParameter: 1, internalQueryPlannerMaxIndexedSolutions: 64});
db.adminCommand({setParameter: 1, internalQueryPlannerEnableHashIntersection: true});

// Index optimization
db.assessments.createIndex({user_id: 1, created_at: -1}, {background: true});
```

#### Cache Optimization
```bash
# Redis performance tuning
redis-cli CONFIG SET maxmemory-policy allkeys-lru
redis-cli CONFIG SET maxmemory-samples 10
redis-cli CONFIG SET timeout 300
```

#### Application Optimization
```python
# Connection pool optimization
MONGODB_SETTINGS = {
    'maxPoolSize': 100,
    'minPoolSize': 10,
    'maxIdleTimeMS': 30000,
    'waitQueueTimeoutMS': 5000
}

REDIS_SETTINGS = {
    'max_connections': 100,
    'socket_timeout': 5,
    'socket_connect_timeout': 5,
    'retry_on_timeout': True
}
```

---

*This configuration guide should be updated whenever new services are added or configuration requirements change.*