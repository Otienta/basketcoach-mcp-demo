# scripts/validate_setup.py
#!/usr/bin/env python3
"""
Script de validation complet de l'installation BasketCoach MCP
"""

import asyncio
import requests
import sys
import os
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from utils.ollama_client import check_ollama_health
from mcp_client import MCPClient

def validate_environment():
    """Valide l'environnement technique"""
    print("🔍 Validation de l'environnement...")
    
    checks = {
        "Fichier de données": ROOT_DIR / "data/processed/all_matches_merged.csv",
        "Configuration": ROOT_DIR / "config.yaml", 
        "Modèle ML": ROOT_DIR / "ml/model/player_impact_predictor.pkl",
    }
    
    for name, path in checks.items():
        exists = path.exists()
        print(f"  {name}: {'✅' if exists else '❌'} {path}")
        if not exists and name == "Fichier de données":
            print("     💡 Exécutez: python utils/data_processor.py")
    
    return all(path.exists() for path in checks.values())

def validate_ollama():
    """Valide la connexion Ollama"""
    print("\n🤖 Validation Ollama...")
    if check_ollama_health():
        print("  ✅ Ollama accessible sur localhost:11434")
        return True
    else:
        print("  ❌ Ollama non détecté")
        print("     💡 Lancez: ollama serve")
        return False

async def validate_mcp_server():
    """Valide le serveur MCP"""
    print("\n🌐 Validation serveur MCP...")
    
    client = MCPClient()
    
    # Test santé serveur
    if client.health_check():
        print("  ✅ Serveur MCP accessible")
        
        # Test outils principaux
        tools_to_test = [
            ("get_player_impact", {"match_id": "2051529", "player_name": "Marine Johannès"}),
            ("ask_coach_ai", {"question": "Test de connexion"}),
            ("get_match_analysis", {"match_id": "2051529"})
        ]
        
        for tool_name, params in tools_to_test:
            try:
                result = client.call_tool(tool_name, **params)
                status = "✅" if "error" not in result else "⚠️"
                print(f"  {status} Outil {tool_name}: {result.get('error', 'Fonctionnel')}")
            except Exception as e:
                print(f"  ❌ Outil {tool_name}: {e}")
                
        return True
    else:
        print("  ❌ Serveur MCP inaccessible")
        print("     💡 Lancez: python basketcoach_mcp_server.py")
        return False

async def main():
    print("🏀 VALIDATION COMPLÈTE BASKETCOACH MCP")
    print("=" * 50)
    
    # 1. Environnement
    env_ok = validate_environment()
    
    # 2. Ollama  
    ollama_ok = validate_ollama()
    
    # 3. Serveur MCP
    mcp_ok = await validate_mcp_server()
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DE VALIDATION:")
    print(f"  Environnement: {'✅' if env_ok else '❌'}")
    print(f"  Ollama: {'✅' if ollama_ok else '❌'}")
    print(f"  Serveur MCP: {'✅' if mcp_ok else '❌'}")
    
    if all([env_ok, ollama_ok, mcp_ok]):
        print("\n🎉 TOUT EST OPÉRATIONNEL! Vous pouvez utiliser BasketCoach MCP")
        print("   Interface: streamlit run app.py")
        print("   API: http://localhost:8000")
    else:
        print("\n⚠️  Des problèmes ont été détectés. Consultez les corrections ci-dessus.")

if __name__ == "__main__":
    asyncio.run(main())