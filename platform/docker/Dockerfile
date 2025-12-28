# Dockerfile for Muppet Platform Service
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV using the official installer
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Add UV to PATH (it installs to ~/.local/bin by default)
ENV PATH="/root/.local/bin:$PATH"

# Create non-root user
RUN useradd --create-home --shell /bin/bash platform

# Copy UV configuration files and README (needed for build)
COPY pyproject.toml uv.lock README.md ./

# Install dependencies using UV
RUN uv sync --frozen --no-dev

# Copy source code
COPY src/ ./src/

# Copy templates directory (needed for template discovery)
COPY ../templates/ /templates/

# Copy terraform modules directory (needed for infrastructure generation)
COPY ../terraform-modules/ /terraform-modules/

# Create logs directory and set permissions
RUN mkdir -p logs && chown -R platform:platform /app

# Make uv available to the platform user by copying to system path
RUN cp /root/.local/bin/uv /usr/local/bin/uv && chmod +x /usr/local/bin/uv

# Switch to non-root user
USER platform

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application using UV
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]