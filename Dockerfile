FROM python:3.12-slim

# Run as a non-root user
RUN useradd --create-home --shell /usr/sbin/nologin appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY config.py fetch.py notifier.py main.py ./

RUN mkdir -p /app/data && chown appuser:appuser /app/data
USER appuser

ENV DATA_DIR=/app/data \
    PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
