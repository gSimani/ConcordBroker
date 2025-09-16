# Florida Daily Updates - Docker Container
# Multi-stage build for optimized production container

# Build stage
FROM python:3.11-slim-bookworm AS builder

# Set build arguments
ARG BUILD_DATE
ARG VERSION=1.0.0
ARG VCS_REF

# Add metadata labels
LABEL maintainer="ConcordBroker Team" \
      version="${VERSION}" \
      description="Florida Property Data Daily Update System" \
      build-date="${BUILD_DATE}" \
      vcs-ref="${VCS_REF}"

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Production stage
FROM python:3.11-slim-bookworm AS production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:$PATH" \
    ENVIRONMENT=production

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    cron \
    supervisor \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r florida && useradd -r -g florida -d /app -s /bin/bash florida

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create application directory structure
RUN mkdir -p /app/florida_daily_updates/{agents,config,data/{downloads,temp,processed,backups},logs,scripts} \
    && chown -R florida:florida /app

# Set working directory
WORKDIR /app

# Copy application files
COPY --chown=florida:florida florida_daily_updates/ /app/florida_daily_updates/

# Create entrypoint script
RUN cat > /app/entrypoint.sh << 'EOF'
#!/bin/bash
set -e

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

log "Starting Florida Daily Updates container..."

# Ensure directories exist and have correct permissions
mkdir -p /app/florida_daily_updates/{data/{downloads,temp,processed,backups},logs}
chown -R florida:florida /app/florida_daily_updates/data /app/florida_daily_updates/logs

# Handle different run modes
case "${1:-daemon}" in
    "setup")
        log "Running setup..."
        exec python /app/florida_daily_updates/scripts/setup.py
        ;;
    "full")
        log "Running full update..."
        exec python /app/florida_daily_updates/scripts/run_daily_update.py --mode full
        ;;
    "monitor")
        log "Running monitor check..."
        exec python /app/florida_daily_updates/scripts/run_daily_update.py --mode monitor
        ;;
    "maintenance")
        log "Running maintenance..."
        exec python /app/florida_daily_updates/scripts/run_daily_update.py --mode maintenance
        ;;
    "test")
        log "Running test..."
        exec python /app/florida_daily_updates/scripts/run_daily_update.py --mode test
        ;;
    "daemon"|"cron")
        log "Starting daemon mode with cron scheduler..."
        
        # Create cron job for the florida user
        cat > /tmp/florida-cron << 'CRONEOF'
# Florida Daily Updates Cron Jobs
0 2 * * * cd /app && python /app/florida_daily_updates/scripts/run_daily_update.py --mode full >> /app/florida_daily_updates/logs/cron.log 2>&1
0 */6 * * * cd /app && python /app/florida_daily_updates/scripts/run_daily_update.py --mode monitor >> /app/florida_daily_updates/logs/cron.log 2>&1
0 3 * * 0 cd /app && python /app/florida_daily_updates/scripts/run_daily_update.py --mode maintenance >> /app/florida_daily_updates/logs/cron.log 2>&1
CRONEOF
        
        # Install crontab for florida user
        chown florida:florida /tmp/florida-cron
        su -c "crontab /tmp/florida-cron" florida
        rm /tmp/florida-cron
        
        # Start cron service
        service cron start
        
        # Keep container running and tail logs
        log "Cron service started. Tailing logs..."
        touch /app/florida_daily_updates/logs/cron.log
        chown florida:florida /app/florida_daily_updates/logs/cron.log
        tail -f /app/florida_daily_updates/logs/cron.log
        ;;
    "shell"|"bash")
        log "Starting shell..."
        exec /bin/bash
        ;;
    *)
        log "Usage: $0 {setup|full|monitor|maintenance|test|daemon|shell}"
        log "Default: daemon"
        exec python /app/florida_daily_updates/scripts/run_daily_update.py --mode full
        ;;
esac
EOF

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Create healthcheck script
RUN cat > /app/healthcheck.sh << 'EOF'
#!/bin/bash
# Simple healthcheck - verify cron is running and logs are being written

# Check if cron is running
if ! pgrep -x "cron" > /dev/null; then
    echo "Cron service is not running"
    exit 1
fi

# Check if log directory is writable
if [ ! -w /app/florida_daily_updates/logs ]; then
    echo "Log directory is not writable"
    exit 1
fi

# Check if we can connect to the database (if configured)
if [ -n "$SUPABASE_URL" ] && [ -n "$SUPABASE_SERVICE_KEY" ]; then
    # Simple connectivity test using Python
    python -c "
import os
import asyncio
from supabase import create_client
try:
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_KEY')
    if url and key:
        client = create_client(url, key)
        print('Database connectivity: OK')
        exit(0)
except Exception as e:
    print(f'Database connectivity: FAILED - {e}')
    exit(1)
"
fi

echo "Health check passed"
exit 0
EOF

RUN chmod +x /app/healthcheck.sh

# Switch to non-root user
USER florida

# Expose ports (if needed for monitoring)
EXPOSE 8080

# Set up health check
HEALTHCHECK --interval=30m --timeout=10s --start-period=5m --retries=3 \
    CMD /app/healthcheck.sh

# Set default command
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["daemon"]

# Add build information
RUN echo "Florida Daily Updates v${VERSION:-1.0.0}" > /app/VERSION \
    && echo "Build Date: ${BUILD_DATE:-unknown}" >> /app/VERSION \
    && echo "VCS Ref: ${VCS_REF:-unknown}" >> /app/VERSION