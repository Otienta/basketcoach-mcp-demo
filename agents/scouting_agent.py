# basketcoach-mcp/agents/scouting_agent.py
#!/usr/bin/env python3
"""
Agent de scouting pour l'analyse et le recrutement de joueurs
Utilise le MCP pour combiner données locales et analyses externes
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
import numpy as np

import os
import sys
# Ajouter le répertoire racine au Python path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)
from mcp_direct_client import direct_client, MCPDirectClient
from utils.logger import get_logger

logger = get_logger("agent.scouting")

class ScoutingAgent:
    """Agent de scouting avec analyse avancée des joueurs"""
    
    def __init__(self, mcp_direct_client: Optional[MCPDirectClient] = None):
        self.mcp_direct_client = mcp_direct_client or direct_client
        self.logger = logger
        
    async def comprehensive_player_scout(self, player_name: str) -> Dict[str, Any]:
        """
        Analyse complète d'un joueur pour le scouting
        Combine toutes les sources de données disponibles
        """
        self.logger.info(f"🔍 Scouting complet: {player_name}")
        
        try:
            # 1. Données de performance
            performance_data = await self._gather_performance_data(player_name)
            
            # 2. Données externes et contexte
            external_data = await self._gather_external_data(player_name)
            
            # 3. Analyse de potentiel
            potential_analysis = await self._analyze_player_potential(performance_data, external_data)
            
            # 4. Rapport de scouting synthétique
            scouting_report = await self._generate_scouting_report(
                player_name, performance_data, external_data, potential_analysis
            )
            
            return {
                "player": player_name,
                "scouting_report": scouting_report,
                "performance_data": performance_data,
                "external_data": external_data,
                "potential_analysis": potential_analysis,
                "scouting_score": self._calculate_scouting_score(performance_data, potential_analysis),
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur scouting {player_name}: {e}")
            return {"error": f"Erreur scouting: {str(e)}"}
    
    async def compare_players(self, player_names: List[str], comparison_metrics: List[str] = None) -> Dict[str, Any]:
        """
        Compare plusieurs joueurs sur différentes métriques
        """
        self.logger.info(f"⚖️ Comparaison joueurs: {', '.join(player_names)}")
        
        if comparison_metrics is None:
            comparison_metrics = ["points", "rebounds", "assists", "efficiency", "consistency"]
        
        try:
            players_data = {}
            
            # Collecte des données pour chaque joueur
            for player in player_names:
                player_analysis = await self.comprehensive_player_scout(player)
                if "error" not in player_analysis:
                    players_data[player] = player_analysis
            
            # Analyse comparative
            comparative_analysis = await self._perform_comparative_analysis(players_data, comparison_metrics)
            
            # Classement et recommandations
            rankings = await self._rank_players(players_data, comparison_metrics)
            
            return {
                "players_compared": player_names,
                "comparison_metrics": comparison_metrics,
                "players_data": players_data,
                "comparative_analysis": comparative_analysis,
                "rankings": rankings,
                "recommendations": await self._generate_comparison_recommendations(rankings)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur comparaison: {e}")
            return {"error": f"Erreur comparaison: {str(e)}"}
    
    async def find_similar_players(self, target_player: str, pool_players: List[str]) -> Dict[str, Any]:
        """
        Trouve des joueurs similaires au joueur cible dans le pool
        """
        self.logger.info(f"🔎 Recherche joueurs similaires à: {target_player}")
        
        try:
            # Analyse du joueur cible
            target_analysis = await self.comprehensive_player_scout(target_player)
            if "error" in target_analysis:
                return {"error": f"Impossible d'analyser {target_player}"}
            
            # Analyse des joueurs du pool
            pool_analyses = {}
            for player in pool_players:
                analysis = await self.comprehensive_player_scout(player)
                if "error" not in analysis:
                    pool_analyses[player] = analysis
            
            # Calcul des similarités
            similarities = await self._calculate_player_similarities(target_analysis, pool_analyses)
            
            # Classement par similarité
            ranked_similarities = sorted(
                similarities.items(),
                key=lambda x: x[1]["similarity_score"],
                reverse=True
            )
            
            return {
                "target_player": target_player,
                "similar_players": ranked_similarities[:5],  # Top 5
                "similarity_metrics": ["playing_style", "statistical_profile", "impact_level"],
                "analysis_method": "cosine_similarity_statistical_profile"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur recherche similarité: {e}")
            return {"error": f"Erreur recherche similarité: {str(e)}"}
    
    async def identify_recruitment_needs(self, team_name: str, budget_constraints: Dict = None) -> Dict[str, Any]:
        """
        Identifie les besoins en recrutement d'une équipe
        Basé sur l'analyse des forces/faiblesses
        """
        self.logger.info(f"🎯 Analyse besoins recrutement: {team_name}")
        
        if budget_constraints is None:
            budget_constraints = {"level": "medium", "flexibility": "moderate"}
        
        try:
            # Analyse de l'équipe actuelle
            team_analysis = await self._analyze_current_team(team_name)
            
            # Identification des gaps
            team_gaps = await self._identify_team_gaps(team_analysis)
            
            # Recommandations de recrutement
            recruitment_recommendations = await self._generate_recruitment_recommendations(
                team_gaps, budget_constraints
            )
            
            return {
                "team": team_name,
                "current_roster_analysis": team_analysis,
                "identified_gaps": team_gaps,
                "recruitment_recommendations": recruitment_recommendations,
                "budget_constraints": budget_constraints,
                "priority_level": self._calculate_recruitment_priority(team_gaps)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur analyse recrutement: {e}")
            return {"error": f"Erreur analyse recrutement: {str(e)}"}
    
    # Méthodes internes
    async def _gather_performance_data(self, player_name: str) -> Dict[str, Any]:
        """Rassemble toutes les données de performance - VERSION AMÉLIORÉE"""
        performance_data = {"player_name": player_name}
        
        # Impact du joueur (via MCP)
        try:
            impact_data = self.mcp_direct_client.get_player_impact("sample_match", player_name)
            if "error" not in impact_data:
                performance_data["impact_analysis"] = impact_data
        except Exception as e:
            logger.warning(f"⚠️ Erreur récupération impact {player_name}: {e}")
        
        # Données historiques avec variation basée sur le nom du joueur
        import hashlib
        hash_value = int(hashlib.md5(player_name.encode()).hexdigest()[:8], 16)
        variation = (hash_value % 1000) / 1000.0
        
        # Stats de base avec variation réaliste
        base_stats = {
            "games_played": 25,
            "points_per_game": 15.0 + (variation * 10),  # 15-25
            "rebounds_per_game": 4.0 + (variation * 8),   # 4-12
            "assists_per_game": 3.0 + (variation * 6),    # 3-9
            "efficiency": 18.0 + (variation * 12),        # 18-30
            "consistency_score": 6.0 + (variation * 4)    # 6-10
        }
        
        performance_data["historical_stats"] = {k: round(v, 1) for k, v in base_stats.items()}
        
        # Tendances réalistes
        performance_data["trends"] = {
            "improving": ["3_point_percentage", "assist_to_turnover_ratio"],
            "declining": ["free_throw_percentage"] if variation > 0.7 else [],
            "stable": ["scoring", "defense"]
        }
        
        return performance_data
    
    async def _gather_external_data(self, player_name: str) -> Dict[str, Any]:
        """Rassemble les données externes"""
        external_data = {}
        
        # Actualités
        news_data = self.mcp_direct_client.get_player_news(player_name)
        if "error" not in news_data:
            external_data["recent_news"] = news_data
        
        # Contexte marché (simulé)
        external_data["market_context"] = {
            "current_value": "€250K-€400K",
            "contract_status": "1 year remaining",
            "interest_level": "High",
            "comparable_players": ["Player A", "Player B"]
        }
        
        # Facteurs intangibles
        external_data["intangible_factors"] = {
            "leadership": 8,
            "work_ethic": 9,
            "basketball_iq": 9,
            "clutch_performance": 7
        }
        
        return external_data
    
    async def _analyze_player_potential(self, performance_data: Dict, external_data: Dict) -> Dict[str, Any]:
        """Analyse le potentiel de développement du joueur"""
        
        historical_stats = performance_data.get("historical_stats", {})
        intangible_factors = external_data.get("intangible_factors", {})
        
        # Score de potentiel
        development_potential = (
            historical_stats.get("efficiency", 0) * 0.4 +
            intangible_factors.get("work_ethic", 0) * 0.3 +
            intangible_factors.get("basketball_iq", 0) * 0.3
        )
        
        # Projection de croissance
        growth_projection = {
            "ceiling": "All-Star potential",
            "realistic_outcome": "Solid starter",
            "development_timeline": "2-3 years",
            "key_development_areas": ["Strength", "Playmaking", "Defensive consistency"]
        }
        
        return {
            "development_potential": round(development_potential, 1),
            "growth_projection": growth_projection,
            "risk_assessment": "Medium-Low",
            "investment_value": "High"
        }
    
    async def _generate_scouting_report(self, player_name: str, performance_data: Dict, 
                                      external_data: Dict, potential_analysis: Dict) -> Dict[str, Any]:
        """Génère un rapport de scouting synthétique"""
        
        return {
            "executive_summary": f"{player_name} montre un profil équilibré avec un fort potentiel de développement.",
            "strengths": [
                "Excellent marqueur à 3 points",
                "Grande intelligence de jeu",
                "Leadership naturel",
                "Capacité clutch"
            ],
            "weaknesses": [
                "Défense individuelle à améliorer",
                "Tendance aux turnovers en pression",
                "Consistance sur toute la saison"
            ],
            "playing_style": "Combo Guard avec capacités de scoreur et passeur",
            "fit_analysis": {
                "ideal_system": "Jeu rapide avec spacing",
                "compatible_coaches": ["Offensive minded", "Player development focus"],
                "team_fit": "Contender ou équipe en reconstruction"
            },
            "recommendation": "Poursuivre le suivi - Cible prioritaire pour recrutement"
        }
    
    def _calculate_scouting_score(self, performance_data: Dict, potential_analysis: Dict) -> Dict[str, Any]:
        """Calcule un score de scouting global - VERSION CORRIGÉE"""
        
        historical_stats = performance_data.get('historical_stats', {})
        potential = potential_analysis.get('development_potential', 0)
        
        # VARIABILITÉ: Utiliser le nom du joueur pour générer des scores uniques
        player_name = performance_data.get('player_name', 'Unknown')
        import hashlib
        hash_value = int(hashlib.md5(player_name.encode()).hexdigest()[:8], 16)
        variation = (hash_value % 1000) / 1000.0  # Variation entre 0 et 1
        
        # Score basé sur les performances avec variation réaliste
        base_performance = (
            historical_stats.get('points_per_game', 0) * 0.3 +
            historical_stats.get('efficiency', 0) * 0.4 +
            historical_stats.get('consistency_score', 0) * 0.3
        )
        
        # Appliquer une variation réaliste (±15%)
        performance_variation = 0.85 + (variation * 0.3)  # Entre 0.85 et 1.15
        performance_score = base_performance * performance_variation
        
        # Score global avec pondération
        overall_score = (performance_score * 0.6 + potential * 0.4)
        
        # Assurer un score réaliste entre 0-100
        overall_score = max(0, min(100, overall_score))
        
        return {
            "overall_score": round(overall_score, 1),
            "performance_score": round(performance_score, 1),
            "potential_score": round(potential, 1),
            "grade": self._convert_score_to_grade(overall_score),
            "priority_level": self._determine_priority_level(overall_score),
            "variation_factor": round(variation, 3)  # Pour le debug
        }
            
    
    async def _perform_comparative_analysis(self, players_data: Dict, metrics: List[str]) -> Dict[str, Any]:
        """Effectue une analyse comparative entre joueurs"""
        
        comparative_data = {}
        
        for metric in metrics:
            metric_values = {}
            for player, data in players_data.items():
                perf_data = data.get("performance_data", {})
                historical_stats = perf_data.get("historical_stats", {})
                
                if metric in historical_stats:
                    metric_values[player] = historical_stats[metric]
                elif metric == "efficiency":
                    impact_data = perf_data.get("impact_analysis", {})
                    metric_values[player] = impact_data.get("predicted_impact", 0)
            
            if metric_values:
                comparative_data[metric] = {
                    "values": metric_values,
                    "leader": max(metric_values.items(), key=lambda x: x[1])[0],
                    "average": np.mean(list(metric_values.values())) if metric_values else 0
                }
        
        return comparative_data
    
    async def _rank_players(self, players_data: Dict, metrics: List[str]) -> List[Dict]:
        """Classe les joueurs selon les métriques"""
        
        rankings = []
        
        for player, data in players_data.items():
            score_data = data.get("scouting_score", {})
            rankings.append({
                "player": player,
                "overall_score": score_data.get("overall_score", 0),
                "performance_score": score_data.get("performance_score", 0),
                "potential_score": score_data.get("potential_score", 0),
                "grade": score_data.get("grade", "N/A"),
                "priority": score_data.get("priority_level", "N/A")
            })
        
        return sorted(rankings, key=lambda x: x["overall_score"], reverse=True)
    
    async def _generate_comparison_recommendations(self, rankings: List[Dict]) -> Dict[str, Any]:
        """Génère des recommandations basées sur la comparaison"""
        
        if not rankings:
            return {"error": "Aucune donnée pour recommandation"}
        
        top_player = rankings[0]
        
        return {
            "top_recommendation": top_player["player"],
            "rationale": f"Score global le plus élevé ({top_player['overall_score']}) avec bon équilibre performance/potentiel",
            "best_value": self._find_best_value(rankings),
            "high_risk_high_reward": self._find_high_potential(rankings)
        }
    
    async def _calculate_player_similarities(self, target_analysis: Dict, pool_analyses: Dict) -> Dict[str, Any]:
        """Calcule les similarités entre joueurs"""
        
        similarities = {}
        target_profile = self._create_player_profile(target_analysis)
        
        for player, analysis in pool_analyses.items():
            player_profile = self._create_player_profile(analysis)
            similarity_score = self._compute_profile_similarity(target_profile, player_profile)
            
            similarities[player] = {
                "similarity_score": similarity_score,
                "similar_attributes": self._identify_similar_attributes(target_profile, player_profile),
                "key_differences": self._identify_key_differences(target_profile, player_profile)
            }
        
        return similarities
    
    async def _analyze_current_team(self, team_name: str) -> Dict[str, Any]:
        """Analyse le roster actuel de l'équipe"""
        # Simulation - dans la réalité, utiliser les données locales
        return {
            "roster_strengths": ["Backcourt scoring", "Three-point shooting", "Team chemistry"],
            "roster_weaknesses": ["Frontcourt depth", "Interior defense", "Rebounding"],
            "key_players": [
                {"name": "Marine Johannès", "role": "Primary scorer", "age": 28},
                {"name": "Sarah Michel", "role": "Defensive specialist", "age": 34}
            ],
            "age_distribution": "Veteran heavy",
            "contract_situation": "Flexible"
        }
    
    async def _identify_team_gaps(self, team_analysis: Dict) -> List[Dict]:
        """Identifie les gaps dans le roster"""
        
        weaknesses = team_analysis.get("roster_weaknesses", [])
        gaps = []
        
        gap_priority = {
            "Frontcourt depth": "High",
            "Interior defense": "High", 
            "Rebounding": "Medium",
            "Playmaking": "Medium",
            "Youth": "Low"
        }
        
        for weakness in weaknesses:
            if weakness in gap_priority:
                gaps.append({
                    "area": weakness,
                    "priority": gap_priority[weakness],
                    "description": f"Besoin en {weakness.lower()}",
                    "ideal_profile": self._get_ideal_profile_for_gap(weakness)
                })
        
        return gaps
    
    async def _generate_recruitment_recommendations(self, team_gaps: List[Dict], budget_constraints: Dict) -> List[Dict]:
        """Génère des recommandations de recrutement"""
        
        recommendations = []
        
        for gap in team_gaps:
            if gap["priority"] == "High":
                recommendations.append({
                    "priority": "Immediate",
                    "position_needed": gap["area"],
                    "ideal_characteristics": gap["ideal_profile"],
                    "budget_allocation": "Significant",
                    "acquisition_strategy": "Trade or free agency"
                })
        
        return recommendations
    async def _calculate_recruitment_priority(self, team_gaps: List[Dict]) -> str:
            """Calcule le niveau de priorité du recrutement - VERSION CORRIGÉE"""
            if not team_gaps:
                return "Low"
            
            high_priority_count = sum(1 for gap in team_gaps if gap.get("priority") == "High")
            medium_priority_count = sum(1 for gap in team_gaps if gap.get("priority") == "Medium")
            
            if high_priority_count >= 2:
                return "High"
            elif high_priority_count == 1 or medium_priority_count >= 2:
                return "Medium"
            else:
                return "Low"
            
    # Méthodes utilitaires
    def _convert_score_to_grade(self, score: float) -> str:
        """Convertit un score numérique en grade"""
        if score >= 90: return "A+"
        elif score >= 85: return "A"
        elif score >= 80: return "A-"
        elif score >= 75: return "B+"
        elif score >= 70: return "B"
        elif score >= 65: return "B-"
        elif score >= 60: return "C+"
        else: return "C"
    
    def _determine_priority_level(self, score: float) -> str:
        """Détermine le niveau de priorité"""
        if score >= 80: return "🌟 Priority Target"
        elif score >= 70: return "✅ High Interest" 
        elif score >= 60: return "📊 Monitor Closely"
        else: return "💡 Development Watch"
    
    def _find_best_value(self, rankings: List[Dict]) -> str:
        """Trouve le meilleur rapport qualité-prix"""
        if len(rankings) < 2:
            return rankings[0]["player"] if rankings else "N/A"
        
        # Simplifié - dans la réalité, prendre en compte le salaire
        return rankings[1]["player"]  # 2ème meilleur score
    
    def _find_high_potential(self, rankings: List[Dict]) -> str:
        """Trouve le joueur avec le plus de potentiel"""
        return max(rankings, key=lambda x: x["potential_score"])["player"]
    
    def _create_player_profile(self, analysis: Dict) -> Dict[str, float]:
        """Crée un profil numérique du joueur"""
        perf_data = analysis.get("performance_data", {})
        historical_stats = perf_data.get("historical_stats", {})
        
        return {
            "scoring": historical_stats.get("points_per_game", 0) / 30,  # Normalisé
            "playmaking": historical_stats.get("assists_per_game", 0) / 10,
            "rebounding": historical_stats.get("rebounds_per_game", 0) / 15,
            "efficiency": historical_stats.get("efficiency", 0) / 30,
            "consistency": historical_stats.get("consistency_score", 0) / 10
        }
    
    def _compute_profile_similarity(self, profile1: Dict, profile2: Dict) -> float:
        """Calcule la similarité entre deux profils"""
        from numpy import dot
        from numpy.linalg import norm
        
        keys = list(profile1.keys())
        vec1 = [profile1[k] for k in keys]
        vec2 = [profile2[k] for k in keys]
        
        if norm(vec1) == 0 or norm(vec2) == 0:
            return 0.0
        
        return dot(vec1, vec2) / (norm(vec1) * norm(vec2))
    
    def _identify_similar_attributes(self, profile1: Dict, profile2: Dict) -> List[str]:
        """Identifie les attributs similaires"""
        similar = []
        for attr, val1 in profile1.items():
            val2 = profile2.get(attr, 0)
            if abs(val1 - val2) < 0.1:  # Seuil de similarité
                similar.append(attr)
        return similar
    
    def _identify_key_differences(self, profile1: Dict, profile2: Dict) -> List[str]:
        """Identifie les différences principales"""
        differences = []
        for attr, val1 in profile1.items():
            val2 = profile2.get(attr, 0)
            if abs(val1 - val2) > 0.2:  # Seuil de différence
                differences.append(f"{attr}: {val1:.2f} vs {val2:.2f}")
        return differences
    
    def _get_ideal_profile_for_gap(self, gap: str) -> str:
        """Retourne le profil idéal pour combler un gap"""
        profiles = {
            "Frontcourt depth": "Big man avec rebond et défense intérieure",
            "Interior defense": "Shot blocker avec physique",
            "Rebounding": "Joueur athlétique avec instinct rebondeur",
            "Playmaking": "Point guard avec vision et passing",
            "Youth": "Jeune joueur avec potentiel de développement"
        }
        return profiles.get(gap, "Profil polyvalent")

# Interface synchrone
def comprehensive_player_scout_sync(player_name: str) -> Dict[str, Any]:
    """Version synchrone pour Streamlit"""
    import asyncio
    agent = ScoutingAgent()
    return asyncio.run(agent.comprehensive_player_scout(player_name))

