# Multi-stage Docker build for Infra Mind
# Learning Note: Multi-stage builds reduce final image size by separating
# build dependencies from runtime dependencies

# Build stage
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY pyproject.toml ./
COPY README.md ./
RUN pip install --upgrade pip setuptools wheel
RUN pip install .

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create non-root user for security
RUN groupadd -r infra_mind && useradd -r -g infra_mind infra_mind

# Create application directory
WORKDIR /app

# Copy application code
COPY src/ ./src/
COPY README.md ./

# Create logs directory
RUN mkdir -p logs && chown -R infra_mind:infra_mind /app

# Switch to non-root user
USER infra_mind

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "src.infra_mind.main:app", "--host", "0.0.0.0", "--port", "8000"]