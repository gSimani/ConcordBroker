# Multi-stage build for ConcordBroker services
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt requirements-data-science.txt ./
RUN pip install --user --no-cache-dir -r requirements.txt && \
    pip install --user --no-cache-dir -r requirements-data-science.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

# Copy application code
COPY --chown=appuser:appuser scripts/ ./scripts/
COPY --chown=appuser:appuser *.json ./
COPY --chown=appuser:appuser *.py ./

# Create necessary directories
RUN mkdir -p logs && chown appuser:appuser logs

# Switch to non-root user
USER appuser

# Health check for main API gateway
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8005/api/health || exit 1

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# Expose ports for all services
EXPOSE 8004 8005 8006

# Start all services via service manager
CMD ["python", "scripts/start_all_services.py"]