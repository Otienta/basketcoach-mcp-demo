# basketcoach-mcp/ml/predict.py
#!/usr/bin/env python3
"""
Module de prédiction pour le modèle d'impact joueur
Intégration avec le serveur MCP
"""

import pandas as pd
import numpy as np
import joblib
import logging
from typing import Dict, Any, List, Optional

from .train import PlayerImpactModel
from utils.logger import get_logger

logger = get_logger("ml.predict")

class Predictor:
    """Classe de prédiction pour l'impact joueur"""
    
    def __init__(self, model_path: str = "ml/model/player_impact_predictor.pkl"):
        self.model_path = model_path
        self.model_wrapper = None
        self.is_loaded = False
        
    def load_model(self):
        """Charge le modèle pré-entraîné"""
        try:
            self.model_wrapper = PlayerImpactModel()
            self.model_wrapper.load_model(self.model_path)
            self.is_loaded = True
            logger.info("✅ Modèle de prédiction chargé")
        except Exception as e:
            logger.error(f"❌ Erreur chargement modèle: {e}")
            self.is_loaded = False
    
    def predict_single_player(self, player_stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prédit l'impact d'un seul joueur - VERSION ROBUSTE POUR PRODUCTION/MCP
        Gère automatiquement toutes les colonnes manquantes + recalcule les features dérivées
        """
        if not self.is_loaded:
            self.load_model()
            if not self.is_loaded:
                return {"error": "Modèle non disponible"}

        try:
            # 1. Valeurs par défaut réalistes (basées sur moyenne LFB)
            defaults = {
                'minutes_played': 25.0,
                'efficiency': 0.0,
                'points_per_minute': 0.0,
                'rebounds_per_minute': 0.0,
                'steals': 1,
                'blocks': 0,
                'turnovers': 2,
                'plus_minus': 0
            }

            # On fusionne avec les stats fournies
            stats = {**defaults, **player_stats}

            # Sécurité : minutes_played ne peut pas être 0
            if stats['minutes_played'] <= 0:
                stats['minutes_played'] = 25.0

            # 2. Recalcul des features dérivées (EXACTEMENT comme dans l'entraînement)
            stats['efficiency'] = (
                stats.get('points', 0) +
                stats.get('rebounds_total', stats.get('rebounds', 0)) +
                stats.get('assists', 0) +
                stats.get('steals', 0) +
                stats.get('blocks', 0) -
                stats.get('turnovers', 0)
            )

            mins = stats['minutes_played']
            stats['points_per_minute'] = stats.get('points', 0) / mins
            stats['rebounds_per_minute'] = stats.get('rebounds_total', stats.get('rebounds',0)) / mins

            # 3. Création du DataFrame avec l'ordre exact des features du modèle
            input_data = pd.DataFrame([{
                'points': stats.get('points', 0),
                'rebounds_total': stats.get('rebounds_total', stats.get('rebounds', 0)),
                'assists': stats.get('assists', 0),
                'steals': stats.get('steals', 0),
                'blocks': stats.get('blocks', 0),
                'turnovers': stats.get('turnovers', 0),
                'plus_minus': stats.get('plus_minus', 0),
                'minutes_played': stats['minutes_played'],
                'efficiency': stats['efficiency'],
                'points_per_minute': stats['points_per_minute'],
                'rebounds_per_minute': stats['rebounds_per_minute']
            }])

            # 4. Prédiction
            impact_score = float(self.model_wrapper.predict(input_data)[0])

            # 5. Interprétation
            interpretation = self._interpret_impact_score(impact_score)

            return {
                "player_name": stats.get('player_name', 'Joueuse anonyme'),
                "predicted_impact": round(impact_score, 2),
                "interpretation": interpretation,
                "confidence": "très haute" if abs(impact_score) > 20 else "haute" if abs(impact_score) > 10 else "moyenne",
                "model_version": "v1.0 (R²=0.995)",
                "features_used": self.model_wrapper.feature_names,
                "source": "local_model + realtime_calculation"
            }

        except Exception as e:
            logger.error(f"Erreur prédiction: {e}")
            import traceback
            traceback.print_exc()
            return {"error": f"Prédiction échouée: {str(e)}"}
    
    def predict_multiple_players(self, players_stats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Prédit l'impact de plusieurs joueurs
        """
        if not self.is_loaded:
            self.load_model()
            if not self.is_loaded:
                return {"error": "Modèle non disponible"}
        
        try:
            results = []
            for player_stats in players_stats:
                result = self.predict_single_player(player_stats)
                results.append(result)
            
            # Classement des joueurs par impact
            successful_results = [r for r in results if "error" not in r]
            ranked_players = sorted(
                successful_results, 
                key=lambda x: x["predicted_impact"], 
                reverse=True
            )
            
            return {
                "total_players": len(players_stats),
                "successful_predictions": len(successful_results),
                "failed_predictions": len(players_stats) - len(successful_results),
                "ranked_players": ranked_players,
                "top_performer": ranked_players[0] if ranked_players else None,
                "analysis_summary": self._generate_analysis_summary(ranked_players)
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur prédiction multiple: {e}")
            return {"error": f"Erreur prédiction multiple: {str(e)}"}
    
    def _interpret_impact_score(self, score: float) -> str:
        """Interprète le score d'impact"""
        thresholds = {
            "très élevé": 25,
            "élevé": 15,
            "moyen": 5,
            "faible": 0
        }
        
        if score >= thresholds["très élevé"]:
            return "Impact très élevé - Joueur clé"
        elif score >= thresholds["élevé"]:
            return "Impact élevé - Contributeur majeur"
        elif score >= thresholds["moyen"]:
            return "Impact moyen - Rôle de soutien"
        else:
            return "Impact faible - Rôle limité"
    
    def _generate_analysis_summary(self, ranked_players: List[Dict]) -> Dict[str, Any]:
        """Génère un résumé de l'analyse"""
        if not ranked_players:
            return {"error": "Aucun joueur à analyser"}
        
        impacts = [p["predicted_impact"] for p in ranked_players]
        
        return {
            "average_impact": float(np.mean(impacts)),
            "max_impact": float(np.max(impacts)),
            "min_impact": float(np.min(impacts)),
            "impact_range": float(np.max(impacts) - np.min(impacts)),
            "recommendation": self._generate_recommendation(ranked_players)
        }
    
    def _generate_recommendation(self, ranked_players: List[Dict]) -> str:
        """Génère une recommandation basée sur l'analyse"""
        if len(ranked_players) < 2:
            return "Données insuffisantes pour une recommandation"
        
        top_player = ranked_players[0]
        second_player = ranked_players[1]
        
        if top_player["predicted_impact"] - second_player["predicted_impact"] > 10:
            return f"{top_player['player_name']} est clairement le meilleur choix"
        else:
            return "Plusieurs joueurs avec des impacts similaires - considérer d'autres facteurs"

# Instance globale pour le serveur MCP
predictor = Predictor()

def predict_player_impact(player_stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fonction principale de prédiction - utilisée par le serveur MCP
    """
    return predictor.predict_single_player(player_stats)

def predict_players_impact(players_stats: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Prédiction pour plusieurs joueurs - utilisée par le serveur MCP
    """
    return predictor.predict_multiple_players(players_stats)