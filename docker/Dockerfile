# Simba API Dockerfile

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

# Install system dependencies for document parsing
RUN apt-get update && apt-get install -y --no-install-recommends \
    # For unstructured document parsing
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    libreoffice \
    pandoc \
    # General utilities
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Copy dependency files first (for caching)
COPY pyproject.toml uv.lock README.md ./

# Install PyTorch CPU-only first (saves ~4GB by avoiding CUDA)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY simba/ ./simba/

# Expose port
EXPOSE 8000

# Default command - run the API server
CMD ["uv", "run", "uvicorn", "simba.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
