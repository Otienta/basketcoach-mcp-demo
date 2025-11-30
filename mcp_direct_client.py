# basketcoach-mcp/mcp_direct_client.py
#!/usr/bin/env python3
"""
Client MCP direct - Version CORRIGÉE pour Streamlit
Gestion robuste de l'asyncio et compatibilité Streamlit
"""
import subprocess
import sys
import json
import logging
from typing import Dict, Any, Optional
import concurrent.futures
import asyncio

logger = logging.getLogger("MCP.Direct")

class MCPDirectClient:
    def __init__(self):
        self.server_process = None
        self.connected = False
        logger.info("Initialisation MCPDirectClient")
    
    def start_server(self):
        """Démarre le serveur MCP en arrière-plan"""
        try:
            self.server_process = subprocess.Popen(
                [sys.executable, "basketcoach_mcp_server.py", "stdio"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True
            )
            logger.info("Serveur MCP démarré")
            return True
        except Exception as e:
            logger.error(f"Erreur démarrage serveur: {e}")
            return False
    
    def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Appel direct d'un outil - version corrigée pour Streamlit"""
        try:
            # Gestion spéciale pour les outils asynchrones dans Streamlit
            if tool_name in ["get_match_analysis", "analyze_match_strategy"]:
                # Utiliser le bon import selon le contexte
                from agents.coaching_agent import analyze_match_strategy_sync
                if tool_name == "get_match_analysis":
                    # Implémentation synchrone pour get_match_analysis
                    return self._get_match_analysis_sync(kwargs.get('match_id'))
                elif tool_name == "analyze_match_strategy":
                    return analyze_match_strategy_sync(kwargs.get('match_id'))
            
            # Pour les autres outils, utiliser asyncio.run() seulement si pas de boucle en cours
            try:
                loop = asyncio.get_running_loop()
                # Boucle déjà en cours - utiliser un ThreadPoolExecutor
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(lambda: asyncio.run(self._call_tool_async(tool_name, **kwargs)))
                    return future.result(timeout=30)
            except RuntimeError:
                # Pas de boucle en cours - utiliser asyncio.run()
                return asyncio.run(self._call_tool_async(tool_name, **kwargs))
                
        except Exception as e:
            logger.error(f"❌ Erreur appel outil {tool_name}: {e}")
            return {"error": str(e)}
    
    async def _call_tool_async(self, tool_name: str, **kwargs):
        """Version asynchrone interne pour tous les outils"""
        try:
            if tool_name == "get_player_impact":
                from basketcoach_mcp_server import get_player_impact
                return await get_player_impact(**kwargs)
            elif tool_name == "get_nba_live_ranking":
                from basketcoach_mcp_server import get_nba_live_ranking
                return await get_nba_live_ranking()
            elif tool_name == "get_nba_player_stats":
                from basketcoach_mcp_server import get_nba_player_stats
                return await get_nba_player_stats(**kwargs)
            elif tool_name == "ask_coach_ai":
                from basketcoach_mcp_server import ask_coach_ai
                return await ask_coach_ai(**kwargs)
            elif tool_name == "generate_coaching_report":
                from basketcoach_mcp_server import generate_coaching_report
                return await generate_coaching_report(**kwargs)
            elif tool_name == "get_team_form":
                from basketcoach_mcp_server import get_team_form
                return await get_team_form(**kwargs)
            elif tool_name == "get_match_analysis":
                from basketcoach_mcp_server import get_match_analysis
                return await get_match_analysis(**kwargs)
            elif tool_name == "get_player_news":
                from basketcoach_mcp_server import get_player_news
                return await get_player_news(**kwargs)
            elif tool_name == "get_training_recommendations":
                from basketcoach_mcp_server import get_training_recommendations
                return await get_training_recommendations(**kwargs)
            elif tool_name == "search_guidelines":
                from basketcoach_mcp_server import search_guidelines
                return await search_guidelines(**kwargs)
            else:
                return {"error": f"Outil {tool_name} non trouvé"}
        except Exception as e:
            logger.error(f"❌ Erreur dans _call_tool_async {tool_name}: {e}")
            return {"error": str(e)}
    
    def _get_match_analysis_sync(self, match_id: str) -> Dict[str, Any]:
        """Version synchrone pour get_match_analysis"""
        try:
            # Implémentation synchrone directe sans asyncio
            import pandas as pd
            from utils.logger import get_logger
            
            logger_sync = get_logger("MCP.sync")
            
            # Charger les données
            try:
                df = pd.read_csv("data/processed/all_matches_merged.csv")
                df['match_id'] = df['match_id'].astype(str)
            except Exception as e:
                return {"error": f"Données non disponibles: {e}"}
            
            # Analyser le match
            match_data = df[df['match_id'] == match_id]
            if match_data.empty:
                return {"error": f"Match {match_id} non trouvé"}
            
            teams = match_data[match_data['is_team']]['team_name'].unique()
            if len(teams) != 2:
                return {"error": "Match incomplet - besoin de 2 équipes"}
            
            team1, team2 = teams
            team1_data = match_data[match_data['team_name'] == team1]
            team2_data = match_data[match_data['team_name'] == team2]
            
            # Top joueurs (non équipes)
            players_data = match_data[~match_data['is_team']]
            top_players = players_data.nlargest(5, 'points')[['player_name', 'points']].to_dict('records')
            
            result = {
                "match_id": match_id,
                "teams": [team1, team2],
                "score": {
                    team1: int(team1_data[team1_data['is_team']]['points'].iloc[0]) if not team1_data[team1_data['is_team']].empty else 0,
                    team2: int(team2_data[team2_data['is_team']]['points'].iloc[0]) if not team2_data[team2_data['is_team']].empty else 0
                },
                "top_players": top_players,
                "analysis_method": "sync_direct"
            }
            
            logger_sync.info(f"✅ Analyse match synchrone: {match_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur _get_match_analysis_sync: {e}")
            return {"error": f"Erreur analyse synchrone: {str(e)}"}
    
    # Méthodes spécifiques pour faciliter l'utilisation (version corrigée)
    def get_player_impact(self, match_id: str, player_name: str) -> Dict[str, Any]:
        """Version corrigée avec gestion d'erreur améliorée"""
        try:
            result = self.call_tool("get_player_impact", match_id=match_id, player_name=player_name)
            
            # Vérification et conversion si nécessaire
            if isinstance(result, str):
                try:
                    return json.loads(result)
                except json.JSONDecodeError:
                    return {"error": f"Réponse invalide: {result}"}
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur get_player_impact: {e}")
            return {"error": str(e)}
    
    def get_nba_live_ranking(self) -> Dict[str, Any]:
        try:
            result = self.call_tool("get_nba_live_ranking")
            if isinstance(result, str):
                return json.loads(result)
            return result
        except Exception as e:
            logger.error(f"❌ Erreur get_nba_live_ranking: {e}")
            return {"error": str(e)}
    
    def get_nba_player_stats(self, player_name: str, season: str = "2024-25") -> Dict[str, Any]:
        try:
            result = self.call_tool("get_nba_player_stats", player_name=player_name, season=season)
            if isinstance(result, str):
                return json.loads(result)
            return result
        except Exception as e:
            logger.error(f"❌ Erreur get_nba_player_stats: {e}")
            return {"error": str(e)}
    
    def ask_coach_ai(self, question: str) -> Dict[str, Any]:
        try:
            result = self.call_tool("ask_coach_ai", question=question)
            if isinstance(result, str):
                return json.loads(result)
            return result
        except Exception as e:
            logger.error(f"❌ Erreur ask_coach_ai: {e}")
            return {"error": str(e)}
    
    def generate_coaching_report(self, match_id: str) -> Dict[str, Any]:
        try:
            result = self.call_tool("generate_coaching_report", match_id=match_id)
            if isinstance(result, str):
                return json.loads(result)
            return result
        except Exception as e:
            logger.error(f"❌ Erreur generate_coaching_report: {e}")
            return {"error": str(e)}
    
    def get_team_form(self, team_name: str, last_matches: int = 5) -> Dict[str, Any]:
        try:
            result = self.call_tool("get_team_form", team_name=team_name, last_matches=last_matches)
            if isinstance(result, str):
                return json.loads(result)
            return result
        except Exception as e:
            logger.error(f"❌ Erreur get_team_form: {e}")
            return {"error": str(e)}
    
    def get_match_analysis(self, match_id: str) -> Dict[str, Any]:
        """Version corrigée avec fallback synchrone"""
        try:
            result = self.call_tool("get_match_analysis", match_id=match_id)
            if isinstance(result, str):
                return json.loads(result)
            return result
        except Exception as e:
            logger.error(f"❌ Erreur get_match_analysis: {e}")
            # Fallback vers la version synchrone
            return self._get_match_analysis_sync(match_id)
    
    def get_player_news(self, player_name: str) -> Dict[str, Any]:
        try:
            result = self.call_tool("get_player_news", player_name=player_name)
            if isinstance(result, str):
                return json.loads(result)
            return result
        except Exception as e:
            logger.error(f"❌ Erreur get_player_news: {e}")
            return {"error": str(e)}
    
    def get_training_recommendations(self, player_name: str) -> Dict[str, Any]:
        try:
            result = self.call_tool("get_training_recommendations", player_name=player_name)
            if isinstance(result, str):
                return json.loads(result)
            return result
        except Exception as e:
            logger.error(f"❌ Erreur get_training_recommendations: {e}")
            return {"error": str(e)}
    
    def search_guidelines(self, query: str) -> Dict[str, Any]:
        try:
            result = self.call_tool("search_guidelines", query=query)
            if isinstance(result, str):
                return json.loads(result)
            return result
        except Exception as e:
            logger.error(f"❌ Erreur search_guidelines: {e}")
            return {"error": str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé du client MCP"""
        try:
            # Test simple avec un outil rapide
            test_result = self.get_nba_live_ranking()
            return {
                "status": "healthy" if "error" not in test_result else "degraded",
                "service": "MCPDirectClient",
                "timestamp": str(subprocess.getoutput('date')),
                "details": test_result.get("error", "All systems operational")
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "MCPDirectClient", 
                "error": str(e)
            }


# Instance globale
direct_client = MCPDirectClient()

# Fonction utilitaire pour le debug
def debug_async_issues():
    """Aide au debug des problèmes asyncio"""
    try:
        loop = asyncio.get_event_loop()
        status = "running" if loop.is_running() else "stopped"
        print(f"🔧 Debug asyncio: Boucle {status}")
        return {"loop_status": status, "loop_running": loop.is_running()}
    except RuntimeError:
        print("🔧 Debug asyncio: Aucune boucle active")
        return {"loop_status": "no_loop"}