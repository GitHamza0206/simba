# docker/Dockerfile

# Build arguments
ARG USE_GPU=false
ARG TARGETARCH
ARG BUILDKIT_INLINE_CACHE=1

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_VERSION=1.7.1 \
    POETRY_NO_INTERACTION=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies with cleanup in the same layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    python3-dev \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    ffmpeg \
    poppler-utils \
    tesseract-ocr && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip install "poetry==$POETRY_VERSION" && \
    poetry --version

# Set working directory
WORKDIR /app

# Copy dependency files
COPY README.md pyproject.toml poetry.lock ./

# Install dependencies and clean cache in same layer
RUN poetry install --no-interaction --no-ansi --no-root && \
    rm -rf ~/.cache/pypoetry/cache ~/.cache/pypoetry/artifacts

# Copy application code (smaller layers at the end)
COPY . .

# Create required directories
RUN mkdir -p /app/uploads /app/markdown /app/vector_stores && \
    chmod -R 755 /app

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
      apt-get clean && \
      rm -rf /var/lib/apt/lists/* && \
      rm -f cuda-keyring_1.0-1_all.deb; \
    fi

# Expose port
EXPOSE 8000

# Start the server with uvicorn
CMD ["python", "-m", "uvicorn", "simba.__main__:create_app", "--host", "0.0.0.0", "--port", "8000", "--factory"]
