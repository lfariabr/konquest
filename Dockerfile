# Build stage
FROM python:3.10-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    python3-dev \
    musl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Upgrade pip and install wheel
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements
COPY requirements.txt .

# Build wheels for all dependencies
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt -v

# Final stage
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE=konquist.settings
ENV PYTHONPATH=/app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    python3-dev \
    musl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy wheels from builder
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

# Install dependencies from wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt -v && \
    rm -rf /wheels

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/media

# Copy project
COPY . .

# Create a non-root user
RUN useradd -m konquest && \
    chown -R konquest:konquest /app
USER konquest

# Command to run on container start
CMD ["gunicorn", "--bind", "0.0.0.0:8001", "konquist.wsgi:application"]