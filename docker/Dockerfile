# Build from the repo root: docker build -f docker/Dockerfile .
FROM python:3.12-slim

# Run as a non-root user
RUN useradd --create-home --shell /usr/sbin/nologin appuser

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir .

RUN mkdir -p /app/data /app/logs && chown appuser:appuser /app/data /app/logs
USER appuser

ENV DATA_DIR=/app/data \
    LOG_DIR=/app/logs \
    PYTHONUNBUFFERED=1

CMD ["firemap"]
