# Official Records Scraper Worker Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies and Playwright dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 worker && chown -R worker:worker /app
USER worker

# Start command
CMD ["python", "worker.py"]