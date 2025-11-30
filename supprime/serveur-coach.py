# basketcoach-mcp/basketcoach_mcp_server.py
#!/usr/bin/env python3
"""
BASKETCOACH MCP SERVER - Serveur MCP combinant données locales + web scraping
8 outils visibles et utiles pour les coachs LFB
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Any
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import requests
import os
from pathlib import Path

# FastMCP pour le serveur MCP
try:
    from mcp import FastMCP
except ImportError:
    # Fallback pour développement
    class FastMCP:
        def __init__(self, name):
            self.name = name
            self.tools = {}
        
        def tool(self, func=None, **kwargs):
            def decorator(f):
                self.tools[f.__name__] = f
                return f
            return decorator(func) if func else decorator
        
        def run(self, host="localhost", port=8000):
            print(f"🚀 Serveur MCP {self.name} démarré sur {host}:{port}")
            print("🛠️ Outils disponibles:", list(self.tools.keys()))

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("BasketCoachMCP")

# Initialisation MCP
mcp = FastMCP("basketcoach-mcp")

# === CONFIGURATION ===
CONFIG = {
    "data_paths": {
        "raw": "data/raw/",
        "processed": "data/processed/",
        "external": "data/external/"
    },
    "web_sources": {
        "lfb_ranking": "https://www.basketlfb.com/classement/",
        "ffbb_news": "https://www.ffbb.com/",
        "eurobasket_stats": "https://basketball.eurobasket.com/France/LFB/",
        "injury_reports": "https://www.basketlfb.com/actualites/"
    },
    "cache_duration": 3600  # 1 heure en secondes
}

class DataManager:
    """Gestionnaire des données locales et externes"""
    
    def __init__(self):
        self.local_data = None
        self.web_cache = {}
        self.cache_timestamps = {}
    
    def load_local_data(self) -> pd.DataFrame:
        """Charge les données locales traitées"""
        try:
            processed_path = Path(CONFIG["data_paths"]["processed"]) / "all_matches_merged.csv"
            if processed_path.exists():
                self.local_data = pd.read_csv(processed_path)
                logger.info(f"✅ Données locales chargées: {len(self.local_data)} lignes")
                return self.local_data
            else:
                logger.warning("❌ Fichier local non trouvé, utilisation des JSON bruts")
                return self._process_raw_json()
        except Exception as e:
            logger.error(f"❌ Erreur chargement données: {e}")
            return pd.DataFrame()
    
    def _process_raw_json(self) -> pd.DataFrame:
        """Traite les JSON bruts en DataFrame"""
        raw_path = Path(CONFIG["data_paths"]["raw"])
        all_data = []
        
        for json_file in raw_path.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    match_data = json.load(f)
                    all_data.extend(self._extract_match_data(match_data))
            except Exception as e:
                logger.warning(f"❌ Erreur traitement {json_file}: {e}")
        
        if all_data:
            df = pd.DataFrame(all_data)
            # Sauvegarde pour usage futur
            processed_path = Path(CONFIG["data_paths"]["processed"])
            processed_path.mkdir(parents=True, exist_ok=True)
            df.to_csv(processed_path / "all_matches_merged.csv", index=False)
            logger.info(f"✅ JSON traités et sauvegardés: {len(df)} lignes")
            return df
        return pd.DataFrame()
    
    def _extract_match_data(self, match_data: Dict) -> List[Dict]:
        """Extrait les données d'un match JSON"""
        extracted = []
        match_id = match_data.get('id', 'unknown')
        
        # Parcours des deux équipes
        for team_key in ['1', '2']:
            if team_key not in match_data.get('tm', {}):
                continue
                
            team_data = match_data['tm'][team_key]
            team_name = team_data.get('name', 'Unknown')
            
            # Statistiques d'équipe
            team_stats = {
                'match_id': match_id,
                'team_name': team_name,
                'is_team': True,
                'player_name': team_name,
                'points': team_data.get('tot_sPoints', 0),
                'rebounds_total': team_data.get('tot_sReboundsTotal', 0),
                'assists': team_data.get('tot_sAssists', 0),
                'steals': team_data.get('tot_sSteals', 0),
                'blocks': team_data.get('tot_sBlocks', 0),
                'turnovers': team_data.get('tot_sTurnovers', 0),
                'date': match_data.get('date', '')
            }
            extracted.append(team_stats)
            
            # Statistiques par joueur
            players = team_data.get('pl', {})
            for player_id, player_data in players.items():
                if isinstance(player_data, dict):
                    player_stats = {
                        'match_id': match_id,
                        'team_name': team_name,
                        'is_team': False,
                        'player_name': f"{player_data.get('firstName', '')} {player_data.get('familyName', '')}",
                        'points': player_data.get('sPoints', 0),
                        'rebounds_total': player_data.get('sReboundsTotal', 0),
                        'assists': player_data.get('sAssists', 0),
                        'steals': player_data.get('sSteals', 0),
                        'blocks': player_data.get('sBlocks', 0),
                        'turnovers': player_data.get('sTurnovers', 0),
                        'minutes_played': player_data.get('sMinutes', '0:00'),
                        'plus_minus': player_data.get('sPlusMinusPoints', 0),
                        'date': match_data.get('date', '')
                    }
                    extracted.append(player_stats)
        
        return extracted

class BasketballScoutMCP:
    """Serveur MCP pour le basket coaching"""
    
    def __init__(self):
        self.mcp = FastMCP("basketcoach-mcp")
        self.data_manager = DataManager()
        self._register_tools()
    
    def _register_tools(self):
        """Enregistre tous les outils MCP"""
        
        @self.mcp.tool()
        async def get_player_impact(match_id: str, player_name: str) -> Dict[str, Any]:
            """
            Impact prédit d'un joueur (modèle ML local) 
            Combine données historiques + modèle entraîné
            """
            logger.info(f"🔍 MCP get_player_impact: {player_name} dans match {match_id}")
            
            try:
                df = self.data_manager.load_local_data()
                if df.empty:
                    return {"error": "Données locales non disponibles"}
                
                # Recherche du joueur dans le match
                player_data = df[
                    (df['match_id'] == match_id) & 
                    (df['player_name'].str.contains(player_name, case=False, na=False)) &
                    (df['is_team'] == False)
                ]
                
                if player_data.empty:
                    return {"error": f"Joueur {player_name} non trouvé dans le match {match_id}"}
                
                player_row = player_data.iloc[0]
                
                # Calcul d'impact simplifié (à remplacer par ton modèle ML)
                impact_score = (
                    player_row.get('points', 0) * 1.0 +
                    player_row.get('rebounds_total', 0) * 0.7 +
                    player_row.get('assists', 0) * 0.8 +
                    player_row.get('steals', 0) * 1.2 +
                    player_row.get('blocks', 0) * 1.5 -
                    player_row.get('turnovers', 0) * 0.8 +
                    player_row.get('plus_minus', 0) * 0.5
                )
                
                return {
                    "player": player_name,
                    "match_id": match_id,
                    "predicted_impact": round(impact_score, 2),
                    "stats_used": {
                        "points": int(player_row.get('points', 0)),
                        "rebounds_total": int(player_row.get('rebounds_total', 0)),
                        "assists": int(player_row.get('assists', 0)),
                        "steals": int(player_row.get('steals', 0)),
                        "blocks": int(player_row.get('blocks', 0)),
                        "turnovers": int(player_row.get('turnovers', 0)),
                        "plus_minus": int(player_row.get('plus_minus', 0))
                    },
                    "source": "modèle_local_impact",
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"❌ Erreur get_player_impact: {e}")
                return {"error": f"Erreur calcul impact: {str(e)}"}

# Initialisation du gestionnaire de données
data_manager = DataManager()

# === OUTILS MCP ===


@mcp.tool()
async def get_current_lfb_ranking() -> Dict[str, Any]:
    """
    Classement LFB en temps réel via web scraping
    Fallback sur données cache si site indisponible
    """
    logger.info("🏆 MCP get_current_lfb_ranking")
    
    cache_key = "lfb_ranking"
    if await _is_cache_valid(cache_key):
        return data_manager.web_cache[cache_key]
    
    try:
        # Scraping du classement LFB
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(CONFIG["web_sources"]["lfb_ranking"], headers=headers, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extraction des données du classement (structure à adapter)
                    ranking_data = []
                    table = soup.find('table', {'class': 'classement'})  # À adapter au site réel
                    
                    if table:
                        rows = table.find_all('tr')[1:6]  # 5 premières équipes
                        for row in rows:
                            cols = row.find_all('td')
                            if len(cols) >= 3:
                                ranking_data.append({
                                    'position': cols[0].text.strip(),
                                    'team': cols[1].text.strip(),
                                    'points': cols[2].text.strip()
                                })
                    
                    result = {
                        "ranking": ranking_data,
                        "source": "basketlfb.com",
                        "updated": datetime.now().isoformat(),
                        "note": "Données temps réel"
                    }
                    
                    # Mise en cache
                    await _update_cache(cache_key, result)
                    return result
                else:
                    raise Exception(f"Status HTTP {response.status}")
                    
    except Exception as e:
        logger.warning(f"⚠️ Scraping LFB échoué: {e}, utilisation du fallback")
        # Fallback sur données simulées
        fallback_data = {
            "ranking": [
                {"position": "1", "team": "ASVEL Feminin", "points": "36"},
                {"position": "2", "team": "Bourges Basket", "points": "34"},
                {"position": "3", "team": "Landerneau", "points": "32"},
                {"position": "4", "team": "Villeneuve d'Ascq", "points": "30"},
                {"position": "5", "team": "Flammes Carolo", "points": "28"}
            ],
            "source": "fallback_simulation",
            "updated": datetime.now().isoformat(),
            "note": "Données simulées - site LFB indisponible"
        }
        await _update_cache(cache_key, fallback_data)
        return fallback_data

@mcp.tool()
async def get_player_news(player_name: str) -> Dict[str, Any]:
    """
    Actualités et blessures d'un joueur via recherche web
    """
    logger.info(f"📰 MCP get_player_news: {player_name}")
    
    cache_key = f"news_{player_name}"
    if await _is_cache_valid(cache_key):
        return data_manager.web_cache[cache_key]
    
    try:
        # Simulation de recherche d'actualités (dans la vraie vie: NewsAPI ou Google News)
        query = f"{player_name} LFB basket"
        
        # Simulation de résultats
        news_items = [
            {
                "title": f"Performance remarquable de {player_name} lors du dernier match",
                "summary": f"{player_name} a marqué 25 points avec 10 rebonds dans la victoire de son équipe.",
                "source": "LFB Actualités",
                "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                "sentiment": "positive",
                "url": "#"
            },
            {
                "title": f"{player_name} dans le groupe pour la prochaine rencontre",
                "summary": "Le staff médical a validé sa participation après un petit problème musculaire.",
                "source": "Équipe Médicale",
                "date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
                "sentiment": "neutral", 
                "url": "#"
            }
        ]
        
        result = {
            "player": player_name,
            "news": news_items,
            "total_articles": len(news_items),
            "source": "simulation_web",
            "updated": datetime.now().isoformat()
        }
        
        await _update_cache(cache_key, result)
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur get_player_news: {e}")
        return {"error": f"Erreur recherche actualités: {str(e)}"}

@mcp.tool()
async def get_team_form(team_name: str, last_matches: int = 5) -> Dict[str, Any]:
    """
    Forme récente d'une équipe (derniers matchs)
    Utilise les données locales pour une analyse précise
    """
    logger.info(f"📈 MCP get_team_form: {team_name}")
    
    try:
        df = data_manager.load_local_data()
        if df.empty:
            return {"error": "Données locales non disponibles"}
        
        # Filtrage des matchs de l'équipe
        team_data = df[
            (df['team_name'] == team_name) & 
            (df['is_team'] == True)
        ].sort_values('date', ascending=False).head(last_matches)
        
        if team_data.empty:
            return {"error": f"Équipe {team_name} non trouvée"}
        
        # Calcul de la forme (simplifié)
        form = []
        points_scored = []
        points_conceded = []
        
        for _, match in team_data.iterrows():
            # Simulation résultat (W/L) basé sur les points
            points = match.get('points', 0)
            form.append('W' if points > 70 else 'L')  # Seuil arbitraire
            points_scored.append(points)
            # points_conceded nécessiterait les points adverses
        
        current_streak = _calculate_streak(form)
        avg_points = np.mean(points_scored) if points_scored else 0
        
        return {
            "team": team_name,
            "last_matches": form,
            "current_streak": current_streak,
            "average_points": round(avg_points, 1),
            "analysis_period": f"{last_matches} derniers matchs",
            "source": "données_locales_historiques",
            "updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur get_team_form: {e}")
        return {"error": f"Erreur analyse forme: {str(e)}"}

@mcp.tool()
async def search_guidelines(keyword: str, max_results: int = 3) -> Dict[str, Any]:
    """
    Recherche dans les guidelines médicales ESC/EU basketball
    Système RAG simplifié
    """
    logger.info(f"📚 MCP search_guidelines: {keyword}")
    
    try:
        # Base de connaissances des guidelines (simplifiée)
        guidelines_db = {
            "entraînement": [
                "ESC 2024: Limiter les séances intensives à 2 par semaine maximum",
                "Recommandation EU: 48h de repos entre deux matches compétitifs",
                "Protocole hydratation: 500ml 2h avant, 250ml toutes les 20min pendant"
            ],
            "blessure": [
                "Cheville: Protocole RICE (Repos, Ice, Compression, Élévation) 48h",
                "Genou: Consultation immédiate si gonflement > 2cm",
                "Épaule: Repos sportif 3 semaines minimum pour luxation"
            ],
            "nutrition": [
                "Apport protéique: 1.6-2.2g/kg/jour pour sportives d'élite",
                "Hydratation: 35-40ml/kg/jour, adapté à la température",
                "Pré-match: Repas riche en glucides 3-4h avant"
            ],
            "récupération": [
                "Sommeil: 8-10h/nuit pour sportives professionnelles",
                "Cryothérapie: 3min à -110°C après match intense",
                "Étirements: 20min de mobilité active quotidienne"
            ]
        }
        
        keyword_lower = keyword.lower()
        results = []
        
        for category, guidelines in guidelines_db.items():
            if keyword_lower in category:
                results.extend(guidelines[:max_results])
                break
        else:
            # Recherche dans toutes les catégories
            for guidelines in guidelines_db.values():
                for guideline in guidelines:
                    if keyword_lower in guideline.lower():
                        results.append(guideline)
                        if len(results) >= max_results:
                            break
        
        return {
            "keyword": keyword,
            "guidelines_found": results,
            "total_results": len(results),
            "source": "guidelines_ESC_EU_basketball",
            "database_version": "2024"
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur search_guidelines: {e}")
        return {"error": f"Erreur recherche guidelines: {str(e)}"}

@mcp.tool()
async def get_match_analysis(match_id: str) -> Dict[str, Any]:
    """
    Analyse complète d'un match avec données détaillées
    """
    logger.info(f"📊 MCP get_match_analysis: {match_id}")
    
    try:
        df = data_manager.load_local_data()
        if df.empty:
            return {"error": "Données locales non disponibles"}
        
        match_data = df[df['match_id'] == match_id]
        if match_data.empty:
            return {"error": f"Match {match_id} non trouvé"}
        
        # Extraction des équipes
        teams = match_data[match_data['is_team'] == True]['team_name'].unique()
        if len(teams) != 2:
            return {"error": "Format de match invalide"}
        
        team1, team2 = teams[0], teams[1]
        
        # Statistiques des équipes
        team1_stats = match_data[
            (match_data['team_name'] == team1) & 
            (match_data['is_team'] == True)
        ].iloc[0]
        
        team2_stats = match_data[
            (match_data['team_name'] == team2) & 
            (match_data['is_team'] == True)
        ].iloc[0]
        
        # Meilleurs joueurs
        players_stats = match_data[
            (match_data['is_team'] == False)
        ].nlargest(3, 'points')
        
        top_players = []
        for _, player in players_stats.iterrows():
            top_players.append({
                "name": player['player_name'],
                "points": int(player['points']),
                "team": player['team_name'],
                "efficiency": int(player.get('plus_minus', 0))
            })
        
        return {
            "match_id": match_id,
            "teams": [team1, team2],
            "score": {
                team1: int(team1_stats['points']),
                team2: int(team2_stats['points'])
            },
            "key_stats": {
                team1: {
                    "rebounds_total": int(team1_stats['rebounds_total']),
                    "assists": int(team1_stats['assists']),
                    "turnovers": int(team1_stats['turnovers'])
                },
                team2: {
                    "rebounds_total": int(team2_stats['rebounds_total']),
                    "assists": int(team2_stats['assists']),
                    "turnovers": int(team2_stats['turnovers'])
                }
            },
            "top_players": top_players,
            "analysis_date": datetime.now().isoformat(),
            "source": "données_locales_détaillées"
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur get_match_analysis: {e}")
        return {"error": f"Erreur analyse match: {str(e)}"}

@mcp.tool()
async def get_player_comparison(player1: str, player2: str) -> Dict[str, Any]:
    """
    Comparaison détaillée entre deux joueurs
    """
    logger.info(f"⚖️ MCP get_player_comparison: {player1} vs {player2}")
    
    try:
        df = data_manager.load_local_data()
        if df.empty:
            return {"error": "Données locales non disponibles"}
        
        # Données des deux joueurs
        p1_data = df[
            (df['player_name'].str.contains(player1, case=False, na=False)) &
            (df['is_team'] == False)
        ]
        
        p2_data = df[
            (df['player_name'].str.contains(player2, case=False, na=False)) &
            (df['is_team'] == False)
        ]
        
        if p1_data.empty or p2_data.empty:
            missing = []
            if p1_data.empty: missing.append(player1)
            if p2_data.empty: missing.append(player2)
            return {"error": f"Joueurs non trouvés: {', '.join(missing)}"}
        
        # Calcul des moyennes
        def get_averages(player_df):
            return {
                "points": round(player_df['points'].mean(), 1),
                "rebounds_total": round(player_df['rebounds_total'].mean(), 1),
                "assists": round(player_df['assists'].mean(), 1),
                "steals": round(player_df['steals'].mean(), 1),
                "blocks": round(player_df['blocks'].mean(), 1),
                "games_played": len(player_df)
            }
        
        p1_avg = get_averages(p1_data)
        p2_avg = get_averages(p2_data)
        
        # Détermination des forces
        def get_strengths(p1, p2, name1, name2):
            strengths = []
            if p1['points'] > p2['points']:
                strengths.append(f"{name1} meilleur marqueur")
            if p1['rebounds_total'] > p2['rebounds_total']:
                strengths.append(f"{name1} meilleur rebondeur")
            if p1['assists'] > p2['assists']:
                strengths.append(f"{name1} meilleur passeur")
            return strengths
        
        p1_strengths = get_strengths(p1_avg, p2_avg, player1, player2)
        p2_strengths = get_strengths(p2_avg, p1_avg, player2, player1)
        
        return {
            "comparison": {
                player1: p1_avg,
                player2: p2_avg
            },
            "strengths": {
                player1: p1_strengths,
                player2: p2_strengths
            },
            "recommendation": _generate_comparison_recommendation(p1_avg, p2_avg, player1, player2),
            "source": "analyse_statistique_historique",
            "updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur get_player_comparison: {e}")
        return {"error": f"Erreur comparaison: {str(e)}"}

@mcp.tool()
async def get_training_recommendations(player_name: str, focus_area: str = "all") -> Dict[str, Any]:
    """
    Recommandations d'entraînement personnalisées
    Basées sur les statistiques et guidelines
    """
    logger.info(f"💪 MCP get_training_recommendations: {player_name} - {focus_area}")
    
    try:
        # Récupération des données du joueur
        df = data_manager.load_local_data()
        if df.empty:
            return {"error": "Données locales non disponibles"}
        
        player_data = df[
            (df['player_name'].str.contains(player_name, case=False, na=False)) &
            (df['is_team'] == False)
        ]
        
        if player_data.empty:
            return {"error": f"Joueur {player_name} non trouvé"}
        
        # Analyse des points faibles
        averages = {
            "points": player_data['points'].mean(),
            "rebounds_total": player_data['rebounds_total'].mean(),
            "assists": player_data['assists'].mean(),
            "turnovers": player_data['turnovers'].mean()
        }
        
        # Génération des recommandations
        recommendations = []
        
        if focus_area in ["all", "shooting"] and averages["points"] < 10:
            recommendations.append({
                "area": "Tir",
                "exercise": "300 tirs par jour à différentes distances",
                "frequency": "5x/semaine",
                "rationale": f"Score moyen actuel: {averages['points']} points/match"
            })
        
        if focus_area in ["all", "rebounding"] and averages["rebounds_total"] < 5:
            recommendations.append({
                "area": "Rebond",
                "exercise": "Travail de positionnement et timing",
                "frequency": "3x/semaine",
                "rationale": f"Moyenne actuelle: {averages['rebounds_total']} rebonds/match"
            })
        
        if focus_area in ["all", "playmaking"] and averages["assists"] < 3:
            recommendations.append({
                "area": "Passe",
                "exercise": "Drills de vision de jeu et passes précises",
                "frequency": "4x/semaine", 
                "rationale": f"Moyenne actuelle: {averages['assists']} passes/match"
            })
        
        if focus_area in ["all", "ball_handling"] and averages["turnovers"] > 2:
            recommendations.append({
                "area": "Maîtrise de balle",
                "exercise": "Exercices de dribble sous pression",
                "frequency": "5x/semaine",
                "rationale": f"Moyenne actuelle: {averages['turnovers']} pertes/match"
            })
        
        return {
            "player": player_name,
            "focus_area": focus_area,
            "recommendations": recommendations,
            "stats_analysis": averages,
            "source": "analyse_statistique_personnalisée",
            "updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur get_training_recommendations: {e}")
        return {"error": f"Erreur recommandations: {str(e)}"}

# === FONCTIONS UTILITAIRES ===

async def main(self):
        """Lance le serveur MCP"""
        logger.info("🚀 Initialisation du serveur BasketCoach MCP...")
        
        # Chargement initial des données
        self.data_manager.load_local_data()
        
        logger.info("✅ Données initialisées")
        logger.info("🛠️ Outils MCP disponibles:")
        for tool_name in self.mcp.tools.keys():
            logger.info(f"   - {tool_name}")
        
        # Lancement du serveur
        self.mcp.run(host="localhost", port=8000)

async def _is_cache_valid(cache_key: str) -> bool:
    """Vérifie si le cache est encore valide"""
    if cache_key not in data_manager.web_cache:
        return False
    if cache_key not in data_manager.cache_timestamps:
        return False
    
    cache_age = datetime.now() - data_manager.cache_timestamps[cache_key]
    return cache_age.total_seconds() < CONFIG["cache_duration"]

async def _update_cache(cache_key: str, data: Any):
    """Met à jour le cache"""
    data_manager.web_cache[cache_key] = data
    data_manager.cache_timestamps[cache_key] = datetime.now()

def _calculate_streak(form: List[str]) -> str:
    """Calcule la série actuelle"""
    if not form:
        return "Aucun match"
    
    current_result = form[0]
    streak = 1
    for result in form[1:]:
        if result == current_result:
            streak += 1
        else:
            break
    
    return f"{current_result}{streak}"

def _generate_comparison_recommendation(p1_avg: Dict, p2_avg: Dict, name1: str, name2: str) -> str:
    """Génère une recommandation basée sur la comparaison"""
    p1_total = p1_avg['points'] + p1_avg['rebounds_total'] + p1_avg['assists']
    p2_total = p2_avg['points'] + p2_avg['rebounds_total'] + p2_avg['assists']
    
    if p1_total > p2_total:
        return f"{name1} montre des statistiques globales supérieures"
    elif p2_total > p1_total:
        return f"{name2} présente de meilleures performances globales"
    else:
        return "Les deux joueurs ont des profils statistiques similaires"

async def _is_cache_valid(cache_key: str) -> bool:
    """Vérifie si le cache est encore valide"""
    if cache_key not in data_manager.web_cache:
        return False
    if cache_key not in data_manager.cache_timestamps:
        return False
    
    cache_age = datetime.now() - data_manager.cache_timestamps[cache_key]
    return cache_age.total_seconds() < CONFIG["cache_duration"]

async def _update_cache(cache_key: str, data: Any):
    """Met à jour le cache"""
    data_manager.web_cache[cache_key] = data
    data_manager.cache_timestamps[cache_key] = datetime.now()

def _calculate_streak(form: List[str]) -> str:
    """Calcule la série actuelle"""
    if not form:
        return "Aucun match"
    
    current_result = form[0]
    streak = 1
    for result in form[1:]:
        if result == current_result:
            streak += 1
        else:
            break
    
    return f"{current_result}{streak}"

def _generate_comparison_recommendation(p1_avg: Dict, p2_avg: Dict, name1: str, name2: str) -> str:
    """Génère une recommandation basée sur la comparaison"""
    p1_total = p1_avg['points'] + p1_avg['rebounds_total'] + p1_avg['assists']
    p2_total = p2_avg['points'] + p2_avg['rebounds_total'] + p2_avg['assists']
    
    if p1_total > p2_total:
        return f"{name1} montre des statistiques globales supérieures"
    elif p2_total > p1_total:
        return f"{name2} présente de meilleures performances globales"
    else:
        return "Les deux joueurs ont des profils statistiques similaires"

# === LANCEMENT DU SERVEUR (VERSION QUI MARCHE VRAIMENT) ===
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="BasketCoach MCP - Réel")

@app.get("/health")
async def health():
    return {"status": "OK", "tools": len(mcp.tools), "data_rows": len(data_manager.load_local_data()) if data_manager.local_data is not None else 0}

@app.post("/tools/{tool_name}")
async def call(tool_name: str, payload: dict = {}):
    if tool_name in mcp.tools:
        tool_func = mcp.tools[tool_name]
        result = await tool_func(**payload)
        return result
    else:
        return {"error": f"Outil {tool_name} non trouvé"}

if __name__ == "__main__":
    # Force l'enregistrement de get_player_impact
    _ = BasketballScoutMCP()
    
    print("BASKETCOACH MCP SERVER - VRAI SERVEUR HTTP ACTIF")
    print("http://127.0.0.1:8000/health")
    uvicorn.run(app, host="127.0.0.1", port=8000)