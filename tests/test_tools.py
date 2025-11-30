# tests/test_tools.py
#!/usr/bin/env python3
import asyncio
import sys
import json
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

async def test_tools():
    """Test rapide que les outils sont bien enregistrés"""
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        
        server_params = StdioServerParameters(
            command="python",
            args=["basketcoach_mcp_server.py", "stdio"]
        )
        
        print("🔌 Connexion au serveur MCP...")
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialisation
                init_result = await session.initialize()
                print(f"✅ Initialisation réussie")
                
                # Lister les outils
                tools_result = await session.list_tools()
                print(f"✅ {len(tools_result.tools)} outils enregistrés:")
                for tool in tools_result.tools:
                    print(f"   • {tool.name}: {tool.description[:100]}...")
                
                # Tester un outil simple
                print("\n🧪 Test de l'outil get_nba_live_ranking...")
                try:
                    result = await session.call_tool("get_nba_live_ranking", {})
                    # Correction: CallToolResult a un attribut 'content'
                    if result.content:
                        # Le contenu est une liste de TextContent, on prend le premier
                        content_text = result.content[0].text
                        # Parser le JSON
                        data = json.loads(content_text)
                        ranking_count = len(data.get('ranking', []))
                        print(f"✅ Test réussi: {ranking_count} équipes récupérées")
                    else:
                        print("❌ Aucun contenu dans la réponse")
                except Exception as e:
                    print(f"⚠️ Test échoué: {e}")
                
                # Test d'un deuxième outil
                print("\n🧪 Test de l'outil ask_coach_ai...")
                try:
                    result = await session.call_tool("ask_coach_ai", {"question": "Comment améliorer la défense ?"})
                    if result.content:
                        content_text = result.content[0].text
                        data = json.loads(content_text)
                        if "answer" in data:
                            print(f"✅ Coach IA: Réponse de {len(data['answer'])} caractères")
                        else:
                            print(f"⚠️ Coach IA: {data.get('error', 'Erreur inconnue')}")
                    else:
                        print("❌ Aucun contenu dans la réponse Coach IA")
                except Exception as e:
                    print(f"⚠️ Test Coach IA échoué: {e}")
                
                return True
                
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_tools())
    sys.exit(0 if success else 1)