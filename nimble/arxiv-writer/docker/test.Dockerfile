# Multi-stage Docker file for testing arxiv-writer package
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy package files
COPY dist/ ./dist/
COPY pyproject.toml ./
COPY README.md ./
COPY LICENSE ./

# Install the package from wheel
RUN pip install --no-cache-dir dist/*.whl

# Test stage
FROM base as test

# Install test dependencies
RUN pip install --no-cache-dir pytest

# Copy test files
COPY tests/ ./tests/
COPY examples/ ./examples/

# Run basic tests
RUN python -c "import arxiv_writer; print('Package imported successfully')"
RUN arxiv-writer --help

# Default command runs tests
CMD ["python", "-m", "pytest", "tests/", "-v", "--tb=short"]

# Production test stage - minimal environment
FROM python:3.11-alpine as production-test

# Install minimal system dependencies
RUN apk add --no-cache git

WORKDIR /app

# Copy and install only the wheel
COPY dist/*.whl ./
RUN pip install --no-cache-dir *.whl

# Test CLI functionality
RUN arxiv-writer --help
RUN python -c "import arxiv_writer; print('Production test passed')"

# Default command
CMD ["arxiv-writer", "--help"]