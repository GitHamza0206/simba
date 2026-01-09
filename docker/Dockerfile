# Simba API Dockerfile

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

# Install system dependencies for document parsing
RUN apt-get update && apt-get install -y --no-install-recommends \
    # For docling document parsing
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    # General utilities
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Copy dependency files first (for caching)
COPY pyproject.toml uv.lock README.md ./

# Install dependencies (skip torch, torchvision, and CUDA packages)
RUN uv sync --frozen --no-dev \
    --no-install-package torch \
    --no-install-package torchvision \
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

# Install CPU-only PyTorch and torchvision into the venv (saves ~4GB by avoiding CUDA)
# torchvision is required by docling-ibm-models for AutoProcessor in transformers
RUN uv pip install --python /app/.venv/bin/python torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Copy application code
COPY simba/ ./simba/

# Expose port
EXPOSE 8000

# Default command - run the API server using the venv's python
CMD ["/app/.venv/bin/python", "-m", "uvicorn", "simba.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
