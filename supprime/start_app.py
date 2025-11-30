# scripts/start_app.py
#!/usr/bin/env python3
"""
Script de démarrage pour BasketCoach MCP + Streamlit
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent

def start_mcp_server():
    """Démarre le serveur MCP"""
    print("🚀 Démarrage du serveur MCP...")
    process = subprocess.Popen(
        [sys.executable, "basketcoach_mcp_server.py", "stdio"],
        cwd=ROOT_DIR
    )
    time.sleep(2)  # Attendre que le serveur soit prêt
    return process

def start_streamlit():
    """Démarre Streamlit"""
    print("🌐 Démarrage de Streamlit...")
    subprocess.run([
        "streamlit", "run", "app.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0"
    ], cwd=ROOT_DIR)

if __name__ == "__main__":
    print("🏀 BasketCoach MCP - Lancement complet")
    
    # Démarrer le serveur MCP
    mcp_process = start_mcp_server()
    
    try:
        # Démarrer Streamlit
        start_streamlit()
    except KeyboardInterrupt:
        print("\n⏹️ Arrêt en cours...")
    finally:
        # Arrêter le serveur MCP
        mcp_process.terminate()
        print("✅ Arrêt terminé")