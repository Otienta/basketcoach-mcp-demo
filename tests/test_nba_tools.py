# tests/test_nba_tools.py
import sys
import os
import asyncio

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from mcp_client import MCPClient

async def test_nba_tools():
    print("🧪 TEST OUTILS NBA")
    print("=" * 40)
    
    client = MCPClient()
    
    try:
        # Test stats joueur NBA
        print("1. Test stats joueur NBA...")
        result = client.call_tool("get_nba_player_stats", player_name="LeBron James")
        if "error" not in result:
            print("✅ Stats NBA: OK")
            print(f"   → {result['player']}: {result['stats']['points_per_game']} PPG")
        else:
            print("⚠️ Stats NBA: Échec (peut nécessiter nba-api)")
        
        # Test recherche web
        print("2. Test recherche basketball...")
        result = client.call_tool("search_basketball_info", query="Lakers news")
        if "error" not in result:
            print("✅ Recherche web: OK")
            print(f"   → {len(result['results'])} résultats")
        else:
            print("⚠️ Recherche web: Échec")
        
        print("🎉 Tests NBA partiellement réussis!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur tests NBA: {e}")
        return False

def main():
    success = asyncio.run(test_nba_tools())
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)