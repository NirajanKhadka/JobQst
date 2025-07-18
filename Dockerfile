# Dockerfile for AutoJobAgent Celery/Flower services
FROM python:3.11-slim

WORKDIR /app

# Copy lean requirements first for better caching
COPY requirements/requirements-lean.txt /app/requirements-lean.txt

# Install only actually used dependencies (much smaller!)
RUN pip install --upgrade pip && \
    pip install -r requirements-lean.txt

# Copy application code
COPY . /app

CMD ["bash"] 