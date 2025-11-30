# basketcoach-mcp/agents/coaching_agent.py
#!/usr/bin/env python3
"""
Agent de coaching intelligent utilisant exclusivement le MCP
Analyse des matchs, stratégies, et recommandations tactiques
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
import asyncio

# Remplacer par
import os
import sys
# Ajouter le répertoire racine au Python path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)
from mcp_direct_client import direct_client, MCPDirectClient
from utils.logger import get_logger

logger = get_logger("agent.coaching")

class CoachingAgent:
    """Agent de coaching avec analyse stratégique via MCP"""
    
    def __init__(self, mcp_direct_client: Optional[MCPDirectClient] = None):
        self.mcp_direct_client = mcp_direct_client or direct_client
        self.logger = logger
        
    async def analyze_match_strategy(self, match_id: str) -> Dict[str, Any]:
        self.logger.info(f"🎯 Analyse stratégique du match {match_id}")
        
        try:
            # 1. Analyse de base du match
            match_analysis = self.mcp_direct_client.get_match_analysis(match_id)  # ← sync OK ici
            if "error" in match_analysis:
                return {"error": f"Erreur analyse match: {match_analysis['error']}"}
            
            # 2. Analyse des équipes
            teams = match_analysis.get("teams", [])
            team_analyses = {}
            
            for team in teams:
                team_players = await self._get_team_players_from_match(match_id, team)
                team_analyses[team] = {
                    "players_analysis": self._analyze_team_players(team_players, match_id),
                    "team_form": self.mcp_direct_client.get_team_form(team)
                }
            
            # 3. Recommandations
            strategy_recommendations = await self._generate_strategy_recommendations(
                match_analysis, team_analyses
            )
            
            return {
                "match_id": match_id,
                "match_analysis": match_analysis,
                "team_analyses": team_analyses,
                "strategy_recommendations": strategy_recommendations,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur analyse stratégique: {e}")
            import traceback
            traceback.print_exc()
            return {"error": f"Erreur analyse stratégique: {str(e)}"}
    
    async def generate_game_plan(self, team_name: str, opponent: str, match_context: Dict) -> Dict[str, Any]:
        """
        Génère un plan de match personnalisé
        """
        self.logger.info(f"📋 Génération plan de match: {team_name} vs {opponent}")
        
        try:
            # 1. Analyse de l'équipe
            team_form = self.mcp_direct_client.get_team_form(team_name)
            opponent_form = self.mcp_direct_client.get_team_form(opponent)
            
            # 2. Recherche de guidelines pertinentes
            guidelines = self.mcp_direct_client.search_guidelines("stratégie défensive")
            
            # 3. Génération du plan
            game_plan = {
                "offensive_strategy": await self._generate_offensive_strategy(team_form, opponent_form),
                "defensive_strategy": await self._generate_defensive_strategy(team_form, opponent_form),
                "key_matchups": await self._identify_key_matchups(team_name, opponent),
                "in_game_adjustments": await self._generate_in_game_adjustments(team_form),
                "guidelines_references": guidelines.get("guidelines_found", [])
            }
            
            return {
                "team": team_name,
                "opponent": opponent,
                "game_plan": game_plan,
                "generated_at": datetime.now().isoformat(),
                "context": match_context
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur génération plan de match: {e}")
            return {"error": f"Erreur génération plan: {str(e)}"}
    
    async def analyze_opponent_tendencies(self, opponent_team: str, last_matches: int = 5) -> Dict[str, Any]:
        """
        Analyse des tendances et patterns d'une équipe adverse
        """
        self.logger.info(f"🔍 Analyse tendances adverses: {opponent_team}")
        
        try:
            # 1. Forme récente
            opponent_form = self.mcp_direct_client.get_team_form(opponent_team, last_matches)
            
            # 2. Analyse des patterns (simplifiée)
            tendencies = {
                "offensive_tendencies": await self._analyze_offensive_tendencies(opponent_form),
                "defensive_tendencies": await self._analyze_defensive_tendencies(opponent_form),
                "key_players_impact": await self._analyze_key_players_impact(opponent_team),
                "game_pace": await self._analyze_game_pace(opponent_form)
            }
            
            # 3. Recommandations défensives
            defensive_recommendations = await self._generate_defensive_recommendations(tendencies)
            
            return {
                "opponent": opponent_team,
                "analysis_period": f"{last_matches} derniers matchs",
                "tendencies": tendencies,
                "defensive_recommendations": defensive_recommendations,
                "updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur analyse tendances: {e}")
            return {"error": f"Erreur analyse tendances: {str(e)}"}
    
    # Méthodes internes
    async def _get_team_players_from_match(self, match_id: str, team_name: str) -> List[str]:
        """Récupère la liste des joueurs d'une équipe dans un match"""
        # Implémentation simplifiée - dans la réalité, extraire des données locales
        return ["Marine Johannès", "Sarah Michel", "Alexia Chartereau"]  # Exemple
    
    def _analyze_team_players(self, players: List[str], match_id: str) -> Dict[str, Any]:
        """Analyse les joueurs - VERSION SYNCHRONE (car MCP client sync)"""
        players_analysis = {}
        
        for player in players:
            try:
                # ← PAS DE AWAIT ICI ! La fonction est synchrone
                impact = self.mcp_direct_client.get_player_impact(match_id, player)
                players_analysis[player] = impact if "error" not in impact else {"error": "non trouvé"}
            except Exception as e:
                players_analysis[player] = {"error": str(e)}
        
        return players_analysis
    
    async def _generate_strategy_recommendations(self, match_analysis: Dict, team_analyses: Dict) -> Dict[str, Any]:
        """Génère des recommandations stratégiques basées sur l'analyse"""
        
        recommendations = {
            "offensive_focus": "Jeu en transition",
            "defensive_focus": "Pression mi-terrain",
            "key_adjustments": [
                "Augmenter le rythme offensif",
                "Renforcer la défense sur périmètre"
            ],
            "player_specific": {}
        }
        
        # Analyse des forces/faiblesses
        for team, analysis in team_analyses.items():
            players_impact = analysis.get("players_analysis", {})
            if players_impact:
                best_player = max(players_impact.items(), 
                                key=lambda x: x[1].get("predicted_impact", 0))
                recommendations["player_specific"][team] = {
                    "key_player": best_player[0],
                    "impact_score": best_player[1].get("predicted_impact", 0)
                }
        
        return recommendations
    
    async def _generate_offensive_strategy(self, team_form: Dict, opponent_form: Dict) -> List[str]:
        """Génère une stratégie offensive"""
        strategies = []
        
        if team_form.get("average_points", 0) > 80:
            strategies.append("Jeu rapide en transition")
        else:
            strategies.append("Jeu placé demi-terrain")
        
        if opponent_form.get("last_matches", []) and opponent_form["last_matches"].count('L') > 3:
            strategies.append("Pression offensive continue")
        
        return strategies
    
    async def _generate_defensive_strategy(self, team_form: Dict, opponent_form: Dict) -> List[str]:
        """Génère une stratégie défensive"""
        strategies = []
        
        strategies.append("Défense individuelle agressive")
        
        if opponent_form.get("average_points", 0) < 70:
            strategies.append("Forcer les tirs extérieurs")
        else:
            strategies.append("Protéger la raquette")
        
        return strategies
    
    async def _identify_key_matchups(self, team: str, opponent: str) -> List[Dict]:
        """Identifie les matchups clés du match"""
        # Simulation - dans la réalité, basé sur les données des joueurs
        return [
            {
                "team_player": "Marine Johannès",
                "opponent_player": "Sarah Michel", 
                "matchup_type": "Marqueuse vs Défenseure",
                "advantage": "léger"
            }
        ]
    
    async def _generate_in_game_adjustments(self, team_form: Dict) -> List[str]:
        """Génère des ajustements en cours de match"""
        adjustments = []
        
        form = team_form.get("last_matches", [])
        if form and form[0] == 'L':
            adjustments.append("Changer de système offensif si en retard de 10 points")
        
        adjustments.extend([
            "Ajuster défense sur le joueur à +15 points",
            "Utiliser time-out après série de 8-0 adverse"
        ])
        
        return adjustments
    
    async def _analyze_offensive_tendencies(self, opponent_form: Dict) -> Dict[str, Any]:
        """Analyse les tendances offensives de l'adversaire"""
        return {
            "primary_play_type": "Pick and Roll",
            "preferred_tempo": "Medium",
            "key_scoring_zones": ["Paint", "Three_Point"],
            "assist_rate": "High"
        }
    
    async def _analyze_defensive_tendencies(self, opponent_form: Dict) -> Dict[str, Any]:
        """Analyse les tendances défensives de l'adversaire"""
        return {
            "primary_defense": "Man-to-Man",
            "press_frequency": "Occasional",
            "help_defense": "Active",
            "rebounding_emphasis": "Defensive"
        }
    
    async def _analyze_key_players_impact(self, team: str) -> List[Dict]:
        """Analyse l'impact des joueurs clés"""
        # Simulation
        return [
            {
                "player": "Marine Johannès",
                "role": "Leader scoreur",
                "impact_areas": ["Scoring", "Playmaking"],
                "weaknesses": ["Turnovers en pression"]
            }
        ]
    
    async def _analyze_game_pace(self, opponent_form: Dict) -> str:
        """Analyse le rythme de jeu préféré"""
        avg_points = opponent_form.get("average_points", 0)
        if avg_points > 85:
            return "Fast"
        elif avg_points > 75:
            return "Medium" 
        else:
            return "Slow"
    
    async def _generate_defensive_recommendations(self, tendencies: Dict) -> List[str]:
        """Génère des recommandations défensives basées sur les tendances"""
        recommendations = []
        
        offensive_tendencies = tendencies.get("offensive_tendencies", {})
        
        if offensive_tendencies.get("primary_play_type") == "Pick and Roll":
            recommendations.append("Switch défensif sur screens")
        
        if offensive_tendencies.get("preferred_tempo") == "Fast":
            recommendations.append("Ralentir le jeu après paniers")
        
        return recommendations

# Interface synchrone pour Streamlit
def analyze_match_strategy_sync(match_id: str) -> Dict[str, Any]:
    """Version synchrone pour Streamlit"""
    agent = CoachingAgent()
    try:
        # Vérifier si une boucle est déjà en cours
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Exécuter dans la boucle existante
        if loop.is_running():
            # Si la boucle tourne déjà, utiliser create_task
            task = asyncio.create_task(agent.analyze_match_strategy(match_id))
            return task.result()  # Attention: peut bloquer
        else:
            return loop.run_until_complete(agent.analyze_match_strategy(match_id))
    except Exception as e:
        return {"error": f"Erreur asyncio: {str(e)}"}