# Build stage
FROM python:3.11-alpine AS builder

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    && rm -rf /var/cache/apk/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install production dependencies
COPY ./backend/requirements.prod.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.prod.txt

# Production stage
FROM python:3.11-alpine AS production

# Install only runtime dependencies
RUN apk add --no-cache \
    libpq \
    && rm -rf /var/cache/apk/*

# Create non-root user
RUN addgroup -g 1001 -S app && \
    adduser -u 1001 -S app -G app

# Copy virtual environment from builder
COPY --from=builder --chown=app:app /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app/src

# Copy application code
COPY --chown=app:app . /app/src

# Switch to non-root user
USER app

EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/api/planets')" || exit 1

CMD ["python", "__main__.py"]
