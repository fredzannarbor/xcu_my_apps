# Development Docker environment for arxiv-writer
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    curl \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-recommended \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY pyproject.toml ./

# Install package in development mode
RUN pip install --no-cache-dir -e ".[dev,latex,docs]"

# Copy source code
COPY . .

# Install package in editable mode
RUN pip install -e .

# Set environment variables
ENV PYTHONPATH=/app/src
ENV ARXIV_WRITER_LOG_LEVEL=INFO

# Create non-root user
RUN useradd -m -u 1000 developer && \
    chown -R developer:developer /app
USER developer

# Default command
CMD ["bash"]