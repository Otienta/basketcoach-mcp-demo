# basketcoach-mcp/scripts/run_mcp_server.py
#!/usr/bin/env python3
"""
Script de lancement du serveur MCP BasketCoach
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Ajout du chemin racine pour les imports
sys.path.append(str(Path(__file__).parent.parent))

from basketcoach_mcp_server import main
from utils.logger import get_logger

logger = get_logger("scripts.mcp_server")

async def run():
    """Fonction principale de lancement du serveur MCP"""
    try:
        logger.info("🏀 Démarrage du serveur BasketCoach MCP...")
        
        # Vérification des données
        data_path = Path("data/processed/all_matches_merged.csv")
        if not data_path.exists():
            logger.warning("⚠️  Aucune donnée traitée trouvée. Le serveur fonctionnera avec des données simulées.")
            logger.info("💡 Exécutez 'python scripts/setup_environment.py' pour traiter les données JSON")
        
        # Lancement du serveur
        await main()
        
    except KeyboardInterrupt:
        logger.info("🛑 Serveur arrêté par l'utilisateur")
    except Exception as e:
        logger.error(f"💥 Erreur critique: {e}")
        sys.exit(1)

"""
Lancement du VRAI serveur MCP BasketCoach (FastAPI)
"""

import uvicorn

if __name__ == "__main__":
    print("BASKETCOACH MCP - SERVEUR HTTP RÉEL")
    print("http://127.0.0.1:8000/health  ← vérifie ici")
    print("Outils MCP : 8 disponibles avec tes vraies données LFB")
    
    uvicorn.run(
        "basketcoach_mcp_server:app",  # ← charge directement l'app FastAPI
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )