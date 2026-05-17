FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD alembic upgrade head && \
    gunicorn app.main:app \
        --workers 2 \
        --worker-class uvicorn.workers.UvicornWorker \
        --bind 0.0.0.0:${PORT:-8000} \
        --timeout 120 \
        --access-logfile - \
        --error-logfile -
