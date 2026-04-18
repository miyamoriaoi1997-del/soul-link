# Soul-Link Docker Image
# Multi-stage build for minimal image size

FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies to a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY src/ ./src/
COPY pyproject.toml ./

# Install the package in editable mode (no build needed, just metadata)
RUN pip install --no-cache-dir -e . --no-deps

# Create directories for persona files and data
RUN mkdir -p /data/personas /data/cache /data/logs

# Set environment variables
ENV SOUL_LINK_HOME=/data
ENV PYTHONUNBUFFERED=1

# Expose Web UI port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8080/health', timeout=5)" || exit 1

# Default command: start Web UI
CMD ["soul-link", "serve", "--host", "0.0.0.0", "--port", "8080"]
