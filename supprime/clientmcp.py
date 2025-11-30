# basketcoach-mcp/mcp_client.py
#!/usr/bin/env python3
"""
BASKETCOACH MCP CLIENT - Client avec logging détaillé pour visualisation MCP
"""

import requests
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import time
import threading

class MCPClient:
    """Client MCP avec logging avancé pour visualisation"""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self.session = requests.Session()
        self.logger = logging.getLogger("MCPClient")
        self.lock = threading.Lock()
        
        # Configuration du logging détaillé
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Appel générique d'un outil MCP avec logging détaillé
        """
        with self.lock:
            start_time = time.time()
            
            self.logger.info(f"🛠️  APPEL MCP: {tool_name}")
            self.logger.info(f"   📤 Paramètres: {kwargs}")
            
            try:
                response = self.session.post(
                    f"{self.server_url}/tools/{tool_name}",
                    json=kwargs,
                    timeout=30
                )
                
                response_time = round(time.time() - start_time, 2)
                
                if response.status_code == 200:
                    result = response.json()
                    self.logger.info(f"   ✅ RÉPONSE MCP ({response_time}s): Outil {tool_name} réussi")
                    self.logger.info(f"   📊 Résultat: {len(str(result))} caractères")
                    
                    # Log détaillé si erreur dans le résultat
                    if "error" in result:
                        self.logger.warning(f"   ⚠️  Erreur dans résultat: {result['error']}")
                    else:
                        self.logger.info(f"   📦 Données retournées: {list(result.keys())}")
                    
                    return result
                else:
                    self.logger.error(f"   ❌ ERREUR HTTP {response.status_code}: {response.text}")
                    return {
                        "error": f"HTTP {response.status_code}",
                        "details": response.text,
                        "tool": tool_name,
                        "timestamp": datetime.now().isoformat()
                    }
                    
            except requests.exceptions.Timeout:
                self.logger.error(f"   ⏰ TIMEOUT: Outil {tool_name} > 30s")
                return {
                    "error": "Timeout - Serveur MCP non répondant",
                    "tool": tool_name,
                    "timestamp": datetime.now().isoformat()
                }
            except requests.exceptions.ConnectionError:
                self.logger.error(f"   🔌 CONNECTION ERROR: Serveur MCP inaccessible à {self.server_url}")
                return {
                    "error": "Serveur MCP inaccessible",
                    "tool": tool_name, 
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                self.logger.error(f"   💥 ERREUR INATTENDUE: {str(e)}")
                return {
                    "error": f"Erreur inattendue: {str(e)}",
                    "tool": tool_name,
                    "timestamp": datetime.now().isoformat()
                }
    
    # Méthodes spécifiques pour chaque outil
    def get_player_impact(self, match_id: str, player_name: str) -> Dict[str, Any]:
        return self.call_tool("get_player_impact", match_id=match_id, player_name=player_name)
    
    def get_current_lfb_ranking(self) -> Dict[str, Any]:
        return self.call_tool("get_current_lfb_ranking")
    
    def get_player_news(self, player_name: str) -> Dict[str, Any]:
        return self.call_tool("get_player_news", player_name=player_name)
    
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