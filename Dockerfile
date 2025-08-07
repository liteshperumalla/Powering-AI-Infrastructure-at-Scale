# Multi-stage Docker build for Infra Mind - Production Optimized
# Learning Note: Multi-stage builds reduce final image size by separating
# build dependencies from runtime dependencies

# Build stage
FROM python:3.11-slim AS builder

# Set build arguments for security scanning
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Set environment variables for build optimization
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies for building with security updates
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    git \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY pyproject.toml requirements.txt ./
COPY README.md ./

# Install uv and use it to create venv and install dependencies
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    /root/.local/bin/uv venv /opt/venv && \
    /root/.local/bin/uv pip install --no-cache -r requirements.txt .


# Security scanning stage (optional)
FROM builder AS security-scan
RUN pip install --no-cache-dir safety bandit \
    && safety check \
    && bandit -r /opt/venv/lib/python3.11/site-packages/ -f json -o /tmp/bandit-report.json || true

# Production stage
FROM python:3.11-slim AS production

# Set build metadata labels
LABEL maintainer="Infra Mind Team" \
      org.opencontainers.image.title="Infra Mind API" \
      org.opencontainers.image.description="AI-powered infrastructure advisory platform" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.source="https://github.com/your-org/infra-mind"

# Set production environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONPATH="/app/src" \
    INFRA_MIND_ENVIRONMENT=production

# Install runtime system dependencies with security updates
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    dumb-init \
    tini \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create non-root user for security with specific UID/GID
RUN groupadd -r -g 1001 infra_mind && \
    useradd -r -g infra_mind -u 1001 -m -d /home/infra_mind infra_mind

# Create application directory with proper permissions
WORKDIR /app

# Copy application code with proper ownership
COPY --chown=infra_mind:infra_mind src/ ./src/
COPY --chown=infra_mind:infra_mind README.md ./

# Create necessary directories with proper permissions
RUN mkdir -p logs tmp cache /home/infra_mind/.cache && \
    chown -R infra_mind:infra_mind /app /home/infra_mind && \
    chmod -R 755 /app && \
    chmod -R 700 /home/infra_mind

# Switch to non-root user
USER infra_mind

# Health check with improved reliability
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Use tini as init system for proper signal handling
ENTRYPOINT ["tini", "--"]

# Run the application with production settings
CMD ["/opt/venv/bin/uvicorn", "src.infra_mind.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--access-log", \
     "--log-level", "info", \
     "--no-server-header"]