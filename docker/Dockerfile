# docker/Dockerfile

# Build arguments
ARG USE_GPU=false
ARG TARGETARCH
ARG BUILDKIT_INLINE_CACHE=1

# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH="/opt/poetry/bin:$PATH"

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN pip install --no-cache-dir grpcio==1.67.1 && \
    poetry install --no-interaction --no-ansi --no-root --only=main

# Stage 2: Runtime
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH="/opt/poetry/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    ffmpeg \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data/uploads /app/data/processed

# Conditionally install CUDA Toolkit
ARG USE_GPU
ARG TARGETARCH
RUN if [ "$USE_GPU" = "true" ] && [ "$TARGETARCH" = "amd64" ]; then \
      apt-get update && \
      apt-get install -y --no-install-recommends wget gnupg && \
      wget https://developer.download.nvidia.com/compute/cuda/repos/debian11/x86_64/cuda-keyring_1.0-1_all.deb && \
      dpkg -i cuda-keyring_1.0-1_all.deb && \
      apt-get update && \
      apt-get install -y --no-install-recommends cuda-toolkit-11-8 && \
      rm -f cuda-keyring_1.0-1_all.deb && \
      apt-get clean && \
      rm -rf /var/lib/apt/lists/*; \
    fi

# Expose port
EXPOSE 5005

# Start the server
CMD ["uvicorn", "simba.__main__:create_app", "--host", "0.0.0.0", "--port", "5005", "--factory"] 