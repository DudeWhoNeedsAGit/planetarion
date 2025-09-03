FROM python:3.11-slim

WORKDIR /app/src

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY ./backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user first
RUN useradd --create-home --shell /bin/bash app

# Copy application code and set ownership in one step
COPY --chown=app:app . /app/src

# Switch to non-root user
USER app

EXPOSE 5000

CMD ["python", "-m", "backend.app"]
