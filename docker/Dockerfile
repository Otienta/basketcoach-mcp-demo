FROM python:3.11-slim

# Variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000
ENV PYTHONPATH=/app

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Création de l'utilisateur et répertoire de travail
RUN useradd --create-home --shell /bin/bash app
WORKDIR /app
COPY . /app

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Configuration des permissions
RUN chown -R app:app /app
USER app

# Création des répertoires nécessaires
RUN mkdir -p /app/data/raw /app/data/processed /app/data/external \
    /app/ml/model /app/logs /app/rag/guidelines /app/rag/embeddings /app/rag/database

# Exposition du port
EXPOSE $PORT

# Commande de démarrage santé
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Commande de démarrage
CMD ["python", "scripts/run_mcp_server.py"]