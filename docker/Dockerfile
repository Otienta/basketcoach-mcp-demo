FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

RUN apt-get update && apt-get install -y --no-install-recommends curl gcc && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .

# Cache pip magique (le truc qui sauve tout)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m app && chown -R app:app /app
USER app

EXPOSE $PORT
HEALTHCHECK CMD curl -f http://localhost:$PORT/health || exit 1

CMD ["python", "scripts/run_mcp_server.py"]