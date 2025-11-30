#!/bin/bash

set -e

echo "🚀 Déploiement de BasketCoach MCP..."

# Variables
ENVIRONMENT=${1:-staging}
DOCKER_COMPOSE_FILE="docker/docker-compose.prod.yml"

echo "📦 Environment: $ENVIRONMENT"
echo "📁 Docker Compose: $DOCKER_COMPOSE_FILE"

# Vérification de la présence du fichier
if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
    echo "❌ Fichier $DOCKER_COMPOSE_FILE non trouvé"
    exit 1
fi

# Arrêt des conteneurs existants
echo "🛑 Arrêt des conteneurs existants..."
docker-compose -f $DOCKER_COMPOSE_FILE down

# Nettoyage des ressources Docker
echo "🧹 Nettoyage des ressources Docker..."
docker system prune -f

# Pull des dernières images
echo "🔻 Pull des dernières images..."
docker-compose -f $DOCKER_COMPOSE_FILE pull

# Démarrage des conteneurs
echo "🎯 Démarrage des conteneurs..."
docker-compose -f $DOCKER_COMPOSE_FILE up -d

# Attente du démarrage
echo "⏳ Attente du démarrage des services..."
sleep 30

# Health checks
echo "🏥 Vérification de la santé des services..."

# Vérification MCP Server
if curl -f http://localhost:8000/health; then
    echo "✅ MCP Server: OK"
else
    echo "❌ MCP Server: Échec"
    exit 1
fi

# Vérification Streamlit
if curl -f http://localhost:8501/_stcore/health; then
    echo "✅ Streamlit: OK"
else
    echo "⚠️ Streamlit: Health check non disponible, vérification alternative..."
    if curl -f http://localhost:8501; then
        echo "✅ Streamlit: Accessible"
    else
        echo "❌ Streamlit: Échec"
        exit 1
    fi
fi

# Vérification MLflow
if curl -f http://localhost:5000; then
    echo "✅ MLflow: OK"
else
    echo "⚠️ MLflow: Non accessible (peut être normal en production)"
fi

echo "✅ Déploiement terminé avec succès!"
echo "🌐 URLs:"
echo "   - Streamlit: http://localhost:8501"
echo "   - MCP Server: http://localhost:8000"
echo "   - MLflow: http://localhost:5000"