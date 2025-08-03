# HashiCorp Vault Configuration for Production
# Learning Note: Vault provides centralized secrets management with encryption and access control

# Storage backend configuration
storage "file" {
  path = "/vault/data"
}

# Listener configuration
listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = 1  # TLS handled by reverse proxy
}

# API configuration
api_addr = "http://0.0.0.0:8200"
cluster_addr = "http://0.0.0.0:8201"

# UI configuration
ui = true

# Logging
log_level = "Info"
log_format = "json"

# Disable memory lock for containers
disable_mlock = true

# Enable raw endpoint for health checks
raw_storage_endpoint = true

# Seal configuration (auto-unseal in production)
# seal "awskms" {
#   region     = "us-east-1"
#   kms_key_id = "your-kms-key-id"
# }

# Plugin directory
plugin_directory = "/vault/plugins"

# Default lease TTL
default_lease_ttl = "168h"  # 7 days
max_lease_ttl = "720h"      # 30 days

# Cluster configuration
cluster_name = "infra-mind-vault"

# Telemetry
telemetry {
  prometheus_retention_time = "30s"
  disable_hostname = true
}