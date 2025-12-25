# Dockerfile for Muppet Platform Service
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including UV
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN pip install uv

# Copy UV configuration files and README (needed for build)
COPY pyproject.toml uv.lock README.md ./

# Install dependencies using UV
RUN uv sync --frozen --no-dev

# Copy source code
COPY src/ ./src/

# Create logs directory
RUN mkdir -p logs

# Create non-root user
RUN useradd --create-home --shell /bin/bash platform
RUN chown -R platform:platform /app
USER platform

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Run the application using UV
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]