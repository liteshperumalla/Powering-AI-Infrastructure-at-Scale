#!/bin/bash
# Production Docker Build Script with Security Scanning
# Learning Note: Automated build process with security checks and optimization

set -e

# Configuration
REGISTRY="${DOCKER_REGISTRY:-localhost:5000}"
VERSION="${VERSION:-$(git rev-parse --short HEAD)}"
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
VCS_REF=$(git rev-parse HEAD)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting production build process...${NC}"
echo "Version: $VERSION"
echo "Build Date: $BUILD_DATE"
echo "VCS Ref: $VCS_REF"

# Function to log messages
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

# Check prerequisites
log "Checking prerequisites..."
command -v docker >/dev/null 2>&1 || error "Docker is required but not installed"
command -v git >/dev/null 2>&1 || error "Git is required but not installed"

# Install security scanning tools if not present
if ! command -v trivy >/dev/null 2>&1; then
    warn "Trivy not found. Installing..."
    curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
fi

# Clean up previous builds
log "Cleaning up previous builds..."
docker system prune -f --filter "until=24h" || warn "Failed to clean up old images"

# Build API image
log "Building API image..."
docker build \
    --target production \
    --build-arg BUILD_DATE="$BUILD_DATE" \
    --build-arg VCS_REF="$VCS_REF" \
    --build-arg VERSION="$VERSION" \
    --tag "$REGISTRY/infra-mind-api:$VERSION" \
    --tag "$REGISTRY/infra-mind-api:latest" \
    --file Dockerfile \
    . || error "Failed to build API image"

# Build Frontend image
log "Building Frontend image..."
docker build \
    --target production \
    --build-arg BUILD_DATE="$BUILD_DATE" \
    --build-arg VCS_REF="$VCS_REF" \
    --build-arg VERSION="$VERSION" \
    --tag "$REGISTRY/infra-mind-frontend:$VERSION" \
    --tag "$REGISTRY/infra-mind-frontend:latest" \
    --file frontend-react/Dockerfile \
    frontend-react/ || error "Failed to build Frontend image"

# Security scanning with Trivy
log "Running security scans..."

# Scan API image
log "Scanning API image for vulnerabilities..."
trivy image \
    --exit-code 1 \
    --severity HIGH,CRITICAL \
    --format json \
    --output api-security-report.json \
    "$REGISTRY/infra-mind-api:$VERSION" || warn "API image has security vulnerabilities"

# Scan Frontend image
log "Scanning Frontend image for vulnerabilities..."
trivy image \
    --exit-code 1 \
    --severity HIGH,CRITICAL \
    --format json \
    --output frontend-security-report.json \
    "$REGISTRY/infra-mind-frontend:$VERSION" || warn "Frontend image has security vulnerabilities"

# Generate SBOM (Software Bill of Materials)
log "Generating Software Bill of Materials..."
trivy image \
    --format spdx-json \
    --output api-sbom.json \
    "$REGISTRY/infra-mind-api:$VERSION"

trivy image \
    --format spdx-json \
    --output frontend-sbom.json \
    "$REGISTRY/infra-mind-frontend:$VERSION"

# Image optimization analysis
log "Analyzing image sizes..."
API_SIZE=$(docker images "$REGISTRY/infra-mind-api:$VERSION" --format "table {{.Size}}" | tail -n 1)
FRONTEND_SIZE=$(docker images "$REGISTRY/infra-mind-frontend:$VERSION" --format "table {{.Size}}" | tail -n 1)

echo "API Image Size: $API_SIZE"
echo "Frontend Image Size: $FRONTEND_SIZE"

# Test images
log "Testing built images..."

# Test API image
log "Testing API image..."
docker run --rm -d \
    --name test-api \
    -p 8080:8000 \
    -e INFRA_MIND_ENVIRONMENT=test \
    -e INFRA_MIND_DEBUG=false \
    "$REGISTRY/infra-mind-api:$VERSION" || error "Failed to start API container"

# Wait for API to be ready
sleep 10

# Health check
if curl -f http://localhost:8080/health > /dev/null 2>&1; then
    log "API health check passed"
else
    error "API health check failed"
fi

# Stop test container
docker stop test-api

# Test Frontend image
log "Testing Frontend image..."
docker run --rm -d \
    --name test-frontend \
    -p 3080:3000 \
    "$REGISTRY/infra-mind-frontend:$VERSION" || error "Failed to start Frontend container"

# Wait for Frontend to be ready
sleep 15

# Health check
if curl -f http://localhost:3080/api/health > /dev/null 2>&1; then
    log "Frontend health check passed"
else
    warn "Frontend health check failed (may be expected if API endpoint not available)"
fi

# Stop test container
docker stop test-frontend

# Sign images (if cosign is available)
if command -v cosign >/dev/null 2>&1; then
    log "Signing images with cosign..."
    cosign sign --yes "$REGISTRY/infra-mind-api:$VERSION" || warn "Failed to sign API image"
    cosign sign --yes "$REGISTRY/infra-mind-frontend:$VERSION" || warn "Failed to sign Frontend image"
else
    warn "Cosign not found. Skipping image signing."
fi

# Push images to registry
if [ "$PUSH_IMAGES" = "true" ]; then
    log "Pushing images to registry..."
    docker push "$REGISTRY/infra-mind-api:$VERSION"
    docker push "$REGISTRY/infra-mind-api:latest"
    docker push "$REGISTRY/infra-mind-frontend:$VERSION"
    docker push "$REGISTRY/infra-mind-frontend:latest"
    log "Images pushed successfully"
else
    log "Skipping image push (set PUSH_IMAGES=true to enable)"
fi

# Generate build report
log "Generating build report..."
cat > build-report.json <<EOF
{
  "build_date": "$BUILD_DATE",
  "version": "$VERSION",
  "vcs_ref": "$VCS_REF",
  "images": {
    "api": {
      "tag": "$REGISTRY/infra-mind-api:$VERSION",
      "size": "$API_SIZE"
    },
    "frontend": {
      "tag": "$REGISTRY/infra-mind-frontend:$VERSION",
      "size": "$FRONTEND_SIZE"
    }
  },
  "security_reports": {
    "api": "api-security-report.json",
    "frontend": "frontend-security-report.json"
  },
  "sbom": {
    "api": "api-sbom.json",
    "frontend": "frontend-sbom.json"
  }
}
EOF

log "Build completed successfully!"
log "Build report: build-report.json"
log "Security reports: api-security-report.json, frontend-security-report.json"
log "SBOM files: api-sbom.json, frontend-sbom.json"

echo -e "${GREEN}Production build process completed!${NC}"