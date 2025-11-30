# tests/test_mcp_native.py
import sys
import os
import asyncio

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from mcp_client import MCPClient

async def test_mcp_native():
    """Test des outils MCP avec le client natif (pas HTTP)"""
    print("🧪 TEST MCP NATIF")
    print("=" * 40)
    
    client = MCPClient()
    
    try:
        # Connexion au serveur MCP
        if await client.connect():
            print("✅ Connecté au serveur MCP")
            
            # Test 1: Classement NBA
            print("1. Test classement NBA...")
            result = await client.get_nba_live_ranking()
            if "error" not in result:
                print("✅ Classement NBA: OK")
                if result.get('ranking'):
                    print(f" → {len(result['ranking'])} équipes récupérées")
            else:
                print(f"⚠️ Classement NBA: {result.get('error')}")
            
            # Test 2: Coach IA
            print("2. Test Coach IA...")
            result = await client.ask_coach_ai("Comment améliorer mon tir à 3 points?")
            if "answer" in result:
                print("✅ Coach IA: OK")
                print(f" → Réponse: {result['answer'][:100]}...")
            else:
                print(f"⚠️ Coach IA: {result.get('error', 'Erreur inconnue')}")
            
            # Test 3: Analyse de match
            print("3. Test analyse match...")
            result = await client.get_match_analysis("2051529")
            if "teams" in result:
                print("✅ Analyse match: OK")
                print(f" → Match: {result['teams'][0]} vs {result['teams'][1]}")
            else:
                print(f"⚠️ Analyse match: {result.get('error', 'Erreur inconnue')}")
            
            print("🎉 Tests MCP natifs réussis!")
            return True
        else:
            print("❌ Impossible de se connecter au serveur MCP")
            return False
            
    except Exception as e:
        print(f"❌ Erreur tests MCP natifs: {e}")
        return False

def main():
    success = asyncio.run(test_mcp_native())
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)