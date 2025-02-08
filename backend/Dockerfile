# --- Builder stage ---
FROM python:3.11-slim AS builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    python3-dev \
    pkg-config \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry via pip
RUN pip install "poetry==$POETRY_VERSION"

# Set working directory
WORKDIR /app

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Install dependencies via Poetry
RUN poetry install --no-interaction --no-ansi --no-root 

# --- Final stage ---
FROM python:3.11-slim

# Installer Tesseract OCR, Poppler et autres dépendances
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    ffmpeg \
    poppler-utils \
    libpoppler-cpp-dev \
    libpoppler-cpp0v5 \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# --- Installation du CUDA Toolkit pour obtenir nvidia-smi ---
RUN apt-get update && apt-get install -y wget gnupg2 && \
    wget https://developer.download.nvidia.com/compute/cuda/repos/debian11/x86_64/cuda-keyring_1.0-1_all.deb && \
    dpkg -i cuda-keyring_1.0-1_all.deb && \
    apt-get update && apt-get install -y cuda-toolkit-11-8 && \
    rm -rf /var/lib/apt/lists/*

# Copier les packages Python construits dans l'étape builder
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Définir le répertoire de travail et copier le reste de l'application
WORKDIR /app
COPY . .

# Créer les répertoires nécessaires et ajuster les permissions
RUN mkdir -p /app/uploads /app/markdown /app/vector_stores && \
    chmod -R 755 /app

EXPOSE 8000

# Démarrer l'application avec uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
