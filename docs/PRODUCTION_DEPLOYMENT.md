# Production Deployment Guide

This guide covers the complete production deployment of Infra Mind using Kubernetes, including CI/CD pipelines, advanced secrets management, and monitoring.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Secrets Management](#secrets-management)
4. [CI/CD Pipeline](#cicd-pipeline)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Monitoring and Observability](#monitoring-and-observability)
7. [Security Hardening](#security-hardening)
8. [Backup and Disaster Recovery](#backup-and-disaster-recovery)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

- **Kubernetes Cluster**: v1.25+ (EKS, GKE, AKS, or self-managed)
- **kubectl**: v1.25+
- **Helm**: v3.10+ (optional but recommended)
- **Docker**: v20.10+
- **Git**: v2.30+

### Required Permissions

- Kubernetes cluster admin access
- Container registry push/pull permissions
- Cloud provider IAM permissions (for secrets management)
- GitHub repository admin access (for CI/CD)

### Cluster Requirements

- **Minimum Nodes**: 3 nodes
- **Node Resources**: 4 vCPU, 16GB RAM per node
- **Storage**: 100GB+ persistent storage
- **Network**: Load balancer support
- **Add-ons**: Ingress controller, cert-manager, metrics-server

## Infrastructure Setup

### 1. Kubernetes Cluster Setup

#### AWS EKS
```bash
# Create EKS cluster
eksctl create cluster \
  --name infra-mind-prod \
  --version 1.28 \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type m5.xlarge \
  --nodes 3 \
  --nodes-min 3 \
  --nodes-max 10 \
  --managed
```

#### Azure AKS
```bash
# Create AKS cluster
az aks create \
  --resource-group infra-mind-rg \
  --name infra-mind-prod \
  --node-count 3 \
  --node-vm-size Standard_D4s_v3 \
  --kubernetes-version 1.28.0 \
  --enable-addons monitoring \
  --generate-ssh-keys
```

#### Google GKE
```bash
# Create GKE cluster
gcloud container clusters create infra-mind-prod \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type n1-standard-4 \
  --cluster-version 1.28 \
  --enable-autoscaling \
  --min-nodes 3 \
  --max-nodes 10
```

### 2. Install Required Add-ons

#### NGINX Ingress Controller
```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.type=LoadBalancer
```

#### cert-manager
```bash
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --version v1.13.0 \
  --set installCRDs=true
```

#### External Secrets Operator
```bash
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets \
  --namespace external-secrets-system \
  --create-namespace
```

#### Metrics Server
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

## Secrets Management

### Option 1: HashiCorp Vault (Recommended)

#### 1. Install Vault
```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm install vault hashicorp/vault \
  --namespace vault \
  --create-namespace \
  --set server.ha.enabled=true \
  --set server.ha.replicas=3
```

#### 2. Initialize and Configure Vault
```bash
# Initialize Vault
kubectl exec vault-0 -n vault -- vault operator init -key-shares=5 -key-threshold=3

# Unseal Vault (repeat for all replicas)
kubectl exec vault-0 -n vault -- vault operator unseal <unseal-key-1>
kubectl exec vault-0 -n vault -- vault operator unseal <unseal-key-2>
kubectl exec vault-0 -n vault -- vault operator unseal <unseal-key-3>

# Enable Kubernetes auth
kubectl exec vault-0 -n vault -- vault auth enable kubernetes

# Configure Kubernetes auth
kubectl exec vault-0 -n vault -- vault write auth/kubernetes/config \
  token_reviewer_jwt="$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
  kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443" \
  kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
```

#### 3. Create Vault Policies and Roles
```bash
# Create policy
kubectl exec vault-0 -n vault -- vault policy write infra-mind-policy - <<EOF
path "secret/data/infra-mind/*" {
  capabilities = ["read"]
}
EOF

# Create role
kubectl exec vault-0 -n vault -- vault write auth/kubernetes/role/infra-mind \
  bound_service_account_names=vault \
  bound_service_account_namespaces=infra-mind \
  policies=infra-mind-policy \
  ttl=24h
```

#### 4. Store Secrets in Vault
```bash
# Application secrets
kubectl exec vault-0 -n vault -- vault kv put secret/infra-mind/app \
  secret_key="your-super-secure-secret-key" \
  openai_api_key="your-openai-api-key"

# Database secrets
kubectl exec vault-0 -n vault -- vault kv put secret/infra-mind/database \
  mongo_username="admin" \
  mongo_password="secure-mongo-password" \
  redis_password="secure-redis-password"

# Cloud provider secrets
kubectl exec vault-0 -n vault -- vault kv put secret/infra-mind/aws \
  access_key_id="your-aws-access-key" \
  secret_access_key="your-aws-secret-key"
```

### Option 2: Cloud Provider Secret Managers

#### AWS Secrets Manager
```bash
# Create secrets in AWS Secrets Manager
aws secretsmanager create-secret \
  --name "infra-mind/app" \
  --description "Infra Mind application secrets" \
  --secret-string '{"secret_key":"your-secret","openai_api_key":"your-key"}'

aws secretsmanager create-secret \
  --name "infra-mind/database" \
  --description "Infra Mind database secrets" \
  --secret-string '{"mongo_password":"password","redis_password":"password"}'
```

#### Azure Key Vault
```bash
# Create Key Vault
az keyvault create \
  --name infra-mind-kv \
  --resource-group infra-mind-rg \
  --location eastus

# Add secrets
az keyvault secret set --vault-name infra-mind-kv --name "secret-key" --value "your-secret"
az keyvault secret set --vault-name infra-mind-kv --name "openai-api-key" --value "your-key"
```

#### Google Secret Manager
```bash
# Create secrets
echo -n "your-secret-key" | gcloud secrets create secret-key --data-file=-
echo -n "your-openai-key" | gcloud secrets create openai-api-key --data-file=-
```

## CI/CD Pipeline

### GitHub Actions Setup

#### 1. Repository Secrets
Configure the following secrets in your GitHub repository:

**Required Secrets:**
- `OPENAI_API_KEY_TEST`: OpenAI API key for testing
- `KUBE_CONFIG_STAGING`: Base64 encoded kubeconfig for staging
- `KUBE_CONFIG_PRODUCTION`: Base64 encoded kubeconfig for production
- `SLACK_WEBHOOK`: Slack webhook URL for notifications

**Optional Secrets:**
- `SNYK_TOKEN`: Snyk token for security scanning
- `CODECOV_TOKEN`: Codecov token for coverage reports

#### 2. Environment Protection Rules

**Staging Environment:**
- Required reviewers: 1
- Wait timer: 0 minutes
- Deployment branches: `develop` branch only

**Production Environment:**
- Required reviewers: 2
- Wait timer: 5 minutes
- Deployment branches: `main` branch only

#### 3. Branch Protection Rules

**Main Branch:**
- Require pull request reviews (2 reviewers)
- Require status checks to pass
- Require branches to be up to date
- Restrict pushes to admins only

**Develop Branch:**
- Require pull request reviews (1 reviewer)
- Require status checks to pass

### Pipeline Workflow

1. **Code Push/PR** → Triggers CI pipeline
2. **Testing** → Unit tests, integration tests, security scans
3. **Build** → Docker images built and pushed to registry
4. **Security Scan** → Container vulnerability scanning
5. **Deploy Staging** → Automatic deployment to staging (develop branch)
6. **Manual Approval** → Required for production deployment
7. **Deploy Production** → Deployment to production (main branch)
8. **Health Checks** → Automated smoke tests
9. **Notifications** → Slack notifications for success/failure

## Kubernetes Deployment

### 1. Deploy Using Script
```bash
# Deploy to staging
./scripts/deploy-k8s.sh staging deploy

# Deploy to production
./scripts/deploy-k8s.sh production deploy
```

### 2. Manual Deployment Steps

#### Create Namespaces
```bash
kubectl apply -f k8s/namespace.yaml
```

#### Deploy Secrets and Configuration
```bash
# Apply configuration
kubectl apply -f k8s/configmap.yaml

# Apply secrets (ensure they're properly configured)
kubectl apply -f k8s/secrets.yaml

# Apply Vault integration (if using Vault)
kubectl apply -f k8s/vault-integration.yaml
```

#### Deploy Database Components
```bash
# Deploy MongoDB
kubectl apply -f k8s/mongodb-deployment.yaml

# Deploy Redis
kubectl apply -f k8s/redis-deployment.yaml

# Wait for databases to be ready
kubectl wait --for=condition=available --timeout=300s deployment/mongodb -n infra-mind
kubectl wait --for=condition=available --timeout=300s deployment/redis -n infra-mind
```

#### Deploy Applications
```bash
# Deploy API
kubectl apply -f k8s/api-deployment.yaml

# Deploy Frontend
kubectl apply -f k8s/frontend-deployment.yaml

# Wait for applications to be ready
kubectl wait --for=condition=available --timeout=600s deployment/infra-mind-api -n infra-mind
kubectl wait --for=condition=available --timeout=600s deployment/infra-mind-frontend -n infra-mind
```

#### Deploy Networking and Scaling
```bash
# Deploy ingress
kubectl apply -f k8s/ingress.yaml

# Deploy HPA (production only)
kubectl apply -f k8s/hpa.yaml
```

### 3. Verify Deployment
```bash
# Check pod status
kubectl get pods -n infra-mind

# Check services
kubectl get services -n infra-mind

# Check ingress
kubectl get ingress -n infra-mind

# Run health checks
kubectl run test-pod --image=curlimages/curl:latest --rm -i --restart=Never -n infra-mind -- \
  curl -f http://infra-mind-api-service:8000/health
```

## Monitoring and Observability

### 1. Prometheus and Grafana
```bash
# Install Prometheus stack
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.adminPassword=admin123
```

### 2. Application Metrics
The application exposes metrics at `/metrics` endpoint. Key metrics include:
- Request duration and count
- Database connection pool status
- Agent execution times
- Cache hit/miss ratios
- Error rates by endpoint

### 3. Logging
```bash
# Install ELK stack or use cloud provider logging
helm repo add elastic https://helm.elastic.co
helm install elasticsearch elastic/elasticsearch --namespace logging --create-namespace
helm install kibana elastic/kibana --namespace logging
helm install filebeat elastic/filebeat --namespace logging
```

### 4. Alerting Rules
Configure alerts for:
- High error rates (>5%)
- High response times (>2s p95)
- Database connection failures
- Pod restart loops
- Resource utilization (>80%)

## Security Hardening

### 1. Network Policies
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: infra-mind-network-policy
  namespace: infra-mind
spec:
  podSelector:
    matchLabels:
      app: infra-mind-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: infra-mind-frontend
    ports:
    - protocol: TCP
      port: 8000
```

### 2. Pod Security Standards
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: infra-mind
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### 3. RBAC Configuration
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: infra-mind
  name: infra-mind-role
rules:
- apiGroups: [""]
  resources: ["secrets", "configmaps"]
  verbs: ["get", "list"]
```

### 4. Security Scanning
- Container image scanning with Trivy
- Dependency vulnerability scanning with Snyk
- Code security scanning with CodeQL
- Infrastructure scanning with Checkov

## Backup and Disaster Recovery

### 1. Database Backups
```bash
# MongoDB backup
kubectl create job --from=cronjob/mongodb-backup mongodb-backup-$(date +%Y%m%d-%H%M%S) -n infra-mind

# Redis backup
kubectl exec deployment/redis -n infra-mind -- redis-cli BGSAVE
```

### 2. Persistent Volume Backups
```bash
# Create volume snapshots
kubectl apply -f - <<EOF
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: mongodb-snapshot-$(date +%Y%m%d)
  namespace: infra-mind
spec:
  source:
    persistentVolumeClaimName: mongodb-pvc
EOF
```

### 3. Disaster Recovery Plan
1. **RTO (Recovery Time Objective)**: 4 hours
2. **RPO (Recovery Point Objective)**: 1 hour
3. **Backup Frequency**: Daily full, hourly incremental
4. **Cross-region replication**: Enabled for critical data
5. **Automated failover**: Configured for database tier

## Troubleshooting

### Common Issues

#### 1. Pod Startup Issues
```bash
# Check pod logs
kubectl logs -f deployment/infra-mind-api -n infra-mind

# Check pod events
kubectl describe pod <pod-name> -n infra-mind

# Check resource constraints
kubectl top pods -n infra-mind
```

#### 2. Database Connection Issues
```bash
# Test MongoDB connection
kubectl exec -it deployment/mongodb -n infra-mind -- mongosh

# Test Redis connection
kubectl exec -it deployment/redis -n infra-mind -- redis-cli ping
```

#### 3. Ingress Issues
```bash
# Check ingress controller logs
kubectl logs -f deployment/ingress-nginx-controller -n ingress-nginx

# Check certificate status
kubectl describe certificate infra-mind-tls -n infra-mind

# Test internal connectivity
kubectl run test-pod --image=curlimages/curl:latest --rm -i --restart=Never -n infra-mind -- \
  curl -v http://infra-mind-api-service:8000/health
```

#### 4. Performance Issues
```bash
# Check resource usage
kubectl top pods -n infra-mind
kubectl top nodes

# Check HPA status
kubectl get hpa -n infra-mind

# Check metrics
kubectl port-forward service/prometheus-server 9090:80 -n monitoring
```

### Emergency Procedures

#### 1. Rollback Deployment
```bash
# Rollback to previous version
kubectl rollout undo deployment/infra-mind-api -n infra-mind
kubectl rollout undo deployment/infra-mind-frontend -n infra-mind
```

#### 2. Scale Down for Maintenance
```bash
# Scale down applications
kubectl scale deployment infra-mind-api --replicas=0 -n infra-mind
kubectl scale deployment infra-mind-frontend --replicas=0 -n infra-mind
```

#### 3. Emergency Database Recovery
```bash
# Restore from backup
kubectl apply -f backup-restore-job.yaml
```

## Performance Optimization

### 1. Resource Tuning
- Monitor resource usage and adjust requests/limits
- Use HPA for automatic scaling
- Implement VPA for right-sizing

### 2. Database Optimization
- Regular index maintenance
- Connection pool tuning
- Query optimization

### 3. Caching Strategy
- Redis cache warming
- CDN for static assets
- Application-level caching

### 4. Network Optimization
- Use service mesh for advanced traffic management
- Implement circuit breakers
- Optimize ingress configuration

## Maintenance

### Regular Tasks
- **Daily**: Check system health, review logs
- **Weekly**: Update dependencies, security patches
- **Monthly**: Performance review, capacity planning
- **Quarterly**: Disaster recovery testing, security audit

### Update Procedures
1. Test updates in staging environment
2. Schedule maintenance window
3. Create backup before updates
4. Apply updates with rolling deployment
5. Verify system health post-update
6. Monitor for 24 hours after update

This comprehensive guide ensures a robust, secure, and scalable production deployment of Infra Mind with proper CI/CD, monitoring, and operational procedures.