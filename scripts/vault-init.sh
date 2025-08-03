#!/bin/bash
# Vault Initialization Script for Production
# Learning Note: Automates Vault setup with proper security policies

set -e

# Wait for Vault to be ready
echo "Waiting for Vault to be ready..."
until vault status > /dev/null 2>&1; do
  sleep 2
done

# Check if Vault is already initialized
if vault status | grep -q "Initialized.*true"; then
  echo "Vault is already initialized"
  exit 0
fi

echo "Initializing Vault..."

# Initialize Vault with 5 key shares and threshold of 3
INIT_OUTPUT=$(vault operator init -key-shares=5 -key-threshold=3 -format=json)

# Extract unseal keys and root token
UNSEAL_KEY_1=$(echo "$INIT_OUTPUT" | jq -r '.unseal_keys_b64[0]')
UNSEAL_KEY_2=$(echo "$INIT_OUTPUT" | jq -r '.unseal_keys_b64[1]')
UNSEAL_KEY_3=$(echo "$INIT_OUTPUT" | jq -r '.unseal_keys_b64[2]')
ROOT_TOKEN=$(echo "$INIT_OUTPUT" | jq -r '.root_token')

# Save keys securely (in production, distribute these securely)
echo "Saving Vault keys and tokens..."
mkdir -p /vault/keys
echo "$INIT_OUTPUT" > /vault/keys/vault-init.json
chmod 600 /vault/keys/vault-init.json

# Unseal Vault
echo "Unsealing Vault..."
vault operator unseal "$UNSEAL_KEY_1"
vault operator unseal "$UNSEAL_KEY_2"
vault operator unseal "$UNSEAL_KEY_3"

# Authenticate with root token
export VAULT_TOKEN="$ROOT_TOKEN"

# Enable audit logging
echo "Enabling audit logging..."
vault audit enable file file_path=/vault/logs/audit.log

# Enable KV secrets engine
echo "Enabling KV secrets engine..."
vault secrets enable -version=2 -path=secret kv

# Create policies for different services
echo "Creating Vault policies..."

# API service policy
vault policy write api-policy - <<EOF
# Allow API service to read its secrets
path "secret/data/api/*" {
  capabilities = ["read"]
}

# Allow API service to read database credentials
path "secret/data/database/*" {
  capabilities = ["read"]
}

# Allow API service to read cloud provider credentials
path "secret/data/cloud/*" {
  capabilities = ["read"]
}

# Allow API service to read LLM API keys
path "secret/data/llm/*" {
  capabilities = ["read"]
}
EOF

# Frontend service policy
vault policy write frontend-policy - <<EOF
# Allow frontend to read its configuration
path "secret/data/frontend/*" {
  capabilities = ["read"]
}
EOF

# Admin policy for secret management
vault policy write admin-policy - <<EOF
# Full access to secrets
path "secret/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Manage auth methods
path "auth/*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}

# Manage policies
path "sys/policies/acl/*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}
EOF

# Enable AppRole authentication
echo "Enabling AppRole authentication..."
vault auth enable approle

# Create AppRole for API service
vault write auth/approle/role/api-role \
    token_policies="api-policy" \
    token_ttl=1h \
    token_max_ttl=4h \
    bind_secret_id=true

# Create AppRole for frontend service
vault write auth/approle/role/frontend-role \
    token_policies="frontend-policy" \
    token_ttl=1h \
    token_max_ttl=4h \
    bind_secret_id=true

# Get role IDs and secret IDs
API_ROLE_ID=$(vault read -field=role_id auth/approle/role/api-role/role-id)
API_SECRET_ID=$(vault write -field=secret_id -f auth/approle/role/api-role/secret-id)

FRONTEND_ROLE_ID=$(vault read -field=role_id auth/approle/role/frontend-role/role-id)
FRONTEND_SECRET_ID=$(vault write -field=secret_id -f auth/approle/role/frontend-role/secret-id)

# Save role IDs and secret IDs
echo "Saving AppRole credentials..."
cat > /vault/keys/approle-credentials.json <<EOF
{
  "api": {
    "role_id": "$API_ROLE_ID",
    "secret_id": "$API_SECRET_ID"
  },
  "frontend": {
    "role_id": "$FRONTEND_ROLE_ID",
    "secret_id": "$FRONTEND_SECRET_ID"
  }
}
EOF
chmod 600 /vault/keys/approle-credentials.json

# Create initial secrets structure
echo "Creating initial secrets structure..."
vault kv put secret/api/database \
    mongodb_url="mongodb://admin:password@mongodb:27017/infra_mind?authSource=admin" \
    redis_url="redis://:password@redis:6379/0"

vault kv put secret/api/jwt \
    secret_key="$(openssl rand -base64 32)" \
    algorithm="HS256" \
    expire_minutes="30"

vault kv put secret/api/encryption \
    key="$(openssl rand -base64 32)"

# Placeholder for cloud credentials (to be updated with real values)
vault kv put secret/cloud/aws \
    access_key_id="PLACEHOLDER" \
    secret_access_key="PLACEHOLDER" \
    region="us-east-1"

vault kv put secret/cloud/azure \
    client_id="PLACEHOLDER" \
    client_secret="PLACEHOLDER" \
    tenant_id="PLACEHOLDER"

vault kv put secret/cloud/gcp \
    service_account_json="{}" \
    project_id="PLACEHOLDER"

# Placeholder for LLM API keys
vault kv put secret/llm/openai \
    api_key="PLACEHOLDER"

vault kv put secret/llm/anthropic \
    api_key="PLACEHOLDER"

echo "Vault initialization completed successfully!"
echo "Root token: $ROOT_TOKEN"
echo "Please securely store the unseal keys and root token."
echo "In production, distribute unseal keys to different administrators."