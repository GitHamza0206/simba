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

# Install dependencies (skip torch since we installed CPU-only version above)
RUN uv sync --frozen --no-dev \
    --no-install-package torch \
    --no-install-package nvidia-cublas-cu12 \
    --no-install-package nvidia-cuda-cupti-cu12 \
    --no-install-package nvidia-cuda-nvrtc-cu12 \
    --no-install-package nvidia-cuda-runtime-cu12 \
    --no-install-package nvidia-cudnn-cu12 \
    --no-install-package nvidia-cufft-cu12 \
    --no-install-package nvidia-cufile-cu12 \
    --no-install-package nvidia-curand-cu12 \
    --no-install-package nvidia-cusolver-cu12 \
    --no-install-package nvidia-cusparse-cu12 \
    --no-install-package nvidia-cusparselt-cu12 \
    --no-install-package nvidia-nccl-cu12 \
    --no-install-package nvidia-nvjitlink-cu12 \
    --no-install-package nvidia-nvshmem-cu12 \
    --no-install-package nvidia-nvtx-cu12 \
    --no-install-package triton

# Copy application code
COPY simba/ ./simba/

# Expose port
EXPOSE 8000

# Default command - run the API server
CMD ["uv", "run", "uvicorn", "simba.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
