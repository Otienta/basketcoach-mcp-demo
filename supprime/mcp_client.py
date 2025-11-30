# basketcoach-mcp/mcp_client.py
#!/usr/bin/env python3
"""
Nouveau client MCP compatible avec FastMCP
"""
import logging
from typing import Dict, Any, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.cli import stdio_client
import asyncio

logger = logging.getLogger("MCPClient")

class FastMCPClient:
    """Client pour FastMCP server"""
    
    def __init__(self, server_script: str = "basketcoach_mcp_server.py"):
        self.server_script = server_script
        self.session: Optional[ClientSession] = None
        
    async def __aenter__(self):
        server_params = StdioServerParameters(
            command="python",
            args=[self.server_script]
        )
        self.session = await stdio_client(server_params)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Appel générique d'outil MCP"""
        if not self.session:
            raise RuntimeError("Client non connecté")
            
        try:
            result = await self.session.call_tool(tool_name, arguments=kwargs)
            return result
        except Exception as e:
            logger.error(f"Erreur appel outil {tool_name}: {e}")
            return {"error": str(e)}
    
    # Méthodes spécifiques pour chaque outil
    async def get_player_impact(self, match_id: str, player_name: str) -> Dict[str, Any]:
        return await self.call_tool("get_player_impact", match_id=match_id, player_name=player_name)
    
    async def get_nba_live_ranking(self) -> Dict[str, Any]:
        return await self.call_tool("get_nba_live_ranking")
    
    async def get_player_news(self, player_name: str) -> Dict[str, Any]:
        return await self.call_tool("get_player_news", player_name=player_name)
    
    async def get_nba_player_stats(self, player_name: str, season: str = "2024-25") -> Dict[str, Any]:
        return await self.call_tool("get_nba_player_stats", player_name=player_name, season=season)
    
    async def get_nba_player_impact(self, player_name: str, season: str = "2024-25") -> Dict[str, Any]:
        return await self.call_tool("get_nba_player_impact", player_name=player_name, season=season)
    
    async def search_basketball_info(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        return await self.call_tool("search_basketball_info", query=query, max_results=max_results)
    
    async def compare_players(self, player1: str, player2: str) -> Dict[str, Any]:
        return await self.call_tool("compare_players", player1=player1, player2=player2)
    
    async def get_team_form(self, team_name: str, last_matches: int = 5) -> Dict[str, Any]:
        return await self.call_tool("get_team_form", team_name=team_name, last_matches=last_matches)
    
    async def get_match_analysis(self, match_id: str) -> Dict[str, Any]:
        return await self.call_tool("get_match_analysis", match_id=match_id)
    
    async def get_training_recommendations(self, player_name: str, focus_area: str = "all") -> Dict[str, Any]:
        return await self.call_tool("get_training_recommendations", player_name=player_name, focus_area=focus_area)
    
    async def ask_coach_ai(self, question: str) -> Dict[str, Any]:
        return await self.call_tool("ask_coach_ai", question=question)
    
    async def generate_coaching_report(self, match_id: str) -> Dict[str, Any]:
        return await self.call_tool("generate_coaching_report", match_id=match_id)

# Wrapper synchrone pour Streamlit
class SyncMCPClient:
    """Client synchrone pour Streamlit"""
    
    def __init__(self):
        self.client = FastMCPClient()
    
    def _run_async(self, coroutine):
        """Exécute une coroutine de manière synchrone"""
        return asyncio.run(coroutine)
    
    def get_player_impact(self, match_id: str, player_name: str) -> Dict[str, Any]:
        return self._run_async(self.client.get_player_impact(match_id, player_name))
    
    def get_nba_live_ranking(self) -> Dict[str, Any]:
        return self._run_async(self.client.get_nba_live_ranking())
    
    def get_player_news(self, player_name: str) -> Dict[str, Any]:
        return self._run_async(self.client.get_player_news(player_name))
    
    
    
    def get_current_lfb_ranking(self) -> Dict[str, Any]:
        return self.call_tool("get_current_lfb_ranking")
    
    
    def get_team_form(self, team_name: str, last_matches: int = 5) -> Dict[str, Any]:
        return self.call_tool("get_team_form", team_name=team_name, last_matches=last_matches)
    
    def search_guidelines(self, keyword: str, max_results: int = 3) -> Dict[str, Any]:
        return self.call_tool("search_guidelines", keyword=keyword, max_results=max_results)
    
    def get_match_analysis(self, match_id: str) -> Dict[str, Any]:
        return self.call_tool("get_match_analysis", match_id=match_id)
    
    def get_player_comparison(self, player1: str, player2: str) -> Dict[str, Any]:
        return self.call_tool("get_player_comparison", player1=player1, player2=player2)
    
    def get_training_recommendations(self, player_name: str, focus_area: str = "all") -> Dict[str, Any]:
        return self.call_tool("get_training_recommendations", player_name=player_name, focus_area=focus_area)
    
    def health_check(self) -> bool:
        """Vérifie que le serveur MCP est accessible"""
        try:
            response = self.session.get(f"{self.server_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
        
    def ask_coach_ai(self, question: str) -> Dict[str, Any]:
        return self.call_tool("ask_coach_ai", question=question)

    def generate_coaching_report(self, match_id: str) -> Dict[str, Any]:
        return self.call_tool("generate_coaching_report", match_id=match_id)

# Instance globale pour l'application
client = MCPClient()