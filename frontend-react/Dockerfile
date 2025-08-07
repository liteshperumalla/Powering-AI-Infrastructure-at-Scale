# Multi-stage Docker build for React frontend - Production Optimized
# Learning Note: Multi-stage builds optimize image size for production

# Build stage
FROM node:20-alpine AS builder

# Set build arguments for security scanning
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Set working directory
WORKDIR /app

# Install security updates
RUN apk update && apk upgrade && apk add --no-cache \
    curl \
    ca-certificates

# Copy package files
COPY package*.json ./

# Install dependencies with npm ci for production builds
RUN npm install --no-audit --no-fund

# Copy source code
COPY . .

# Build the application with optimizations
ENV DISABLE_ESLINT_PLUGIN=true
RUN npm run build && \
    npm prune --production

# Security scanning stage (optional)
FROM builder AS security-scan
RUN npm audit --audit-level=high || true

# Production stage
FROM node:20-alpine AS production

# Set build metadata labels
LABEL maintainer="Infra Mind Team" \
      org.opencontainers.image.title="Infra Mind Frontend" \
      org.opencontainers.image.description="React frontend for Infra Mind platform" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.source="https://github.com/your-org/infra-mind"

# Set production environment variables
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000

# Install runtime dependencies and security updates
RUN apk update && apk upgrade && apk add --no-cache \
    dumb-init \
    tini \
    curl \
    ca-certificates \
    wget \
    && rm -rf /var/cache/apk/*

# Create non-root user with specific UID/GID
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001 -G nodejs

# Set working directory
WORKDIR /app

# Copy built application from builder stage with proper ownership
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

# Create necessary directories with proper permissions
RUN mkdir -p /app/.next/cache && \
    chown -R nextjs:nodejs /app && \
    chmod -R 755 /app

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Health check with improved reliability
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

# Use tini as init system for proper signal handling
ENTRYPOINT ["tini", "--"]

# Start the application
CMD ["node", "server.js"]

# Development stage
FROM node:20-alpine AS development

WORKDIR /app

RUN apk update && apk upgrade && apk add --no-cache \
    curl \
    ca-certificates

COPY package*.json ./

RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
