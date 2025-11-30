#!/usr/bin/env python3
"""
Lancement simple et direct du serveur MCP corrigé
"""
import sys
from pathlib import Path

# Ajout du chemin racine pour les imports
sys.path.append(str(Path(__file__).parent.parent))

from basketcoach_mcp_server import mcp
from utils.logger import get_logger

logger = get_logger("scripts.mcp_server")

if __name__ == "__main__":
    print("🚀 BASKETCOACH MCP SERVEUR – VERSION STANDARD MCP")
    print("📍 Serveur MCP démarré avec transport stdio")
    print("🛠️  Outils MCP : 12 disponibles avec modèle ML réel !")
    print("🔌 Utilisez le client MCP natif pour vous connecter")
    
    # Lancement du serveur MCP standard (stdio, pas HTTP)
    mcp.run()