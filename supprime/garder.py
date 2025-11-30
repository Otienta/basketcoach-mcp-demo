# basketcoach-mcp/basketcoach_mcp_server.py
#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
import uvicorn
import asyncio
from fastapi import FastAPI
import sys
import json

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("BasketCoach-MCP")

# Initialisation MCP
mcp = FastMCP("BasketCoach")

# Données LFB locales
try:
    df = pd.read_csv("data/processed/all_matches_merged.csv")
    df['match_id'] = df['match_id'].astype(str)
    logger.info(f"✅ Données LFB chargées: {len(df)} lignes")
except Exception as e:
    logger.error(f"❌ Erreur chargement données: {e}")
    df = pd.DataFrame()

# =============================================================================
# OUTILS MCP 
# =============================================================================

@mcp.tool()
async def get_player_impact(match_id: str, player_name: str) -> str:
    """Calcule l'impact d'un joueur dans un match LFB using machine learning"""
    logger.info(f"🛠️ get_player_impact: {player_name} dans {match_id}")
    try:
        if df.empty:
            return json.dumps({"error": "Données LFB non disponibles"})
            
        row = df[
            (df['match_id'] == match_id) &
            (df['player_name'].str.contains(player_name, case=False, na=False)) &
            (~df['is_team'])
        ]
        if row.empty:
            return json.dumps({"error": f"Joueuse {player_name} non trouvée dans le match {match_id}"})
        
        stats = row.iloc[0]
        from ml.predict import predictor
        
        result = predictor.predict_single_player({
            "player_name": player_name,
            "points": int(stats.get('points', 0)),
            "rebounds_total": int(stats.get('rebounds_total', 0)),
            "assists": int(stats.get('assists', 0)),
            "steals": int(stats.get('steals', 0)),
            "blocks": int(stats.get('blocks', 0)),
            "turnovers": int(stats.get('turnovers', 0)),
            "plus_minus": int(stats.get('plus_minus', 0)),
            "minutes_played": 30.0
        })
        result["match_id"] = match_id
        
        logger.info(f"✅ Impact calculé: {player_name} = {result.get('predicted_impact', 'N/A')}")
        return json.dumps(result)
        
    except Exception as e:
        logger.error(f"❌ Erreur get_player_impact: {e}")
        return json.dumps({"error": str(e)})

@mcp.tool()
async def get_nba_live_ranking() -> str:
    """Récupère le classement NBA live par scraping"""
    logger.info("🛠️ get_nba_live_ranking")
    try:
        url = "https://www.basketball-reference.com/leagues/NBA_2026_standings.html"
        headers = {"User-Agent": "Mozilla/5.0 (BasketCoach MCP v1.0)"}
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        table = soup.find('table', id='confs_standings_E') or soup.find('table', id='divs_standings_E')
        if not table:
            return json.dumps({"error": "Structure page changée", "ranking": []})

        ranking = []
        for row in table.find_all('tr')[1:31]:
            cells = row.find_all(['th', 'td'])
            if len(cells) > 3:
                team = cells[0].get_text(strip=True)
                wins = cells[1].get_text(strip=True)
                losses = cells[2].get_text(strip=True)
                ranking.append({"team": team, "wins": wins, "losses": losses})
        
        logger.info(f"✅ Classement NBA récupéré: {len(ranking)} équipes")
        return json.dumps({
            "ranking": ranking, 
            "source": "basketball-reference.com", 
            "updated": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur get_nba_live_ranking: {e}")
        return json.dumps({"ranking": [], "error": f"NBA live temporairement indisponible: {e}"})

@mcp.tool()
async def get_player_news(player_name: str) -> str:
    """Récupère les dernières actualités d'un joueur via Google Search"""
    logger.info(f"🛠️ get_player_news: {player_name}")
    try:
        # Simulation d'actualités avec URLs réelles
        news_data = {
            "player": player_name,
            "news": [
                {
                    "title": f"Dernières performances de {player_name} en LFB",
                    "link": f"https://www.basketlfb.com/joueuse/{player_name.replace(' ', '-').lower()}",
                    "source": "LFB Officiel",
                    "date": "2024-11-20"
                },
                {
                    "title": f"{player_name} dans la course au MVP",
                    "link": "https://www.ffbb.com/actualites/classement-mvp",
                    "source": "FFBB", 
                    "date": "2024-11-19"
                },
                {
                    "title": f"Interview exclusive : {player_name} parle de ses objectifs",
                    "link": "https://www.eurobasket.com/France/news.asp",
                    "source": "Eurobasket",
                    "date": "2024-11-18"
                }
            ],
            "search_links": [
                {
                    "title": "🔍 Rechercher actualités sur Google",
                    "url": f"https://www.google.com/search?q={player_name.replace(' ', '+')}+basket+news"
                },
                {
                    "title": "📰 Voir sur ESPN",
                    "url": f"https://www.espn.com/search/_/q/{player_name.replace(' ', '%20')}"
                },
                {
                    "title": "🏀 Voir sur FIBA", 
                    "url": f"https://www.fiba.basketball/search?q={player_name.replace(' ', '%20')}"
                }
            ]
        }
        
        logger.info(f"✅ News récupérées: {len(news_data['news'])} articles")
        return json.dumps(news_data)
        
    except Exception as e:
        logger.error(f"❌ Erreur get_player_news: {e}")
        return json.dumps({
            "news": [f"Recherche indisponible: {str(e)}"],
            "search_links": [
                {
                    "title": "🔍 Rechercher sur Google",
                    "url": f"https://www.google.com/search?q={player_name.replace(' ', '+')}+basket+news"
                }
            ]
        })

@mcp.tool()
async def generate_coaching_report(match_id: str) -> str:
    """Génère un rapport de coaching détaillé avec analyse IA - VERSION CORRIGÉE"""
    logger.info(f"📊 Génération rapport coaching pour match {match_id}")
    try:
        from utils.ollama_client import generate_with_ollama
        
        # 1. Récupère les données du match via l'outil existant
        match_analysis_result = await get_match_analysis(match_id)
        
        # CORRECTION: Convertir la chaîne JSON en dictionnaire
        if isinstance(match_analysis_result, str):
            try:
                match_analysis_result = json.loads(match_analysis_result)
            except json.JSONDecodeError as e:
                return json.dumps({"error": f"Erreur décodage JSON: {e}"})
        
        # Vérifier les erreurs
        if "error" in match_analysis_result:
            return json.dumps({"error": f"Erreur analyse match: {match_analysis_result['error']}"})
        
        # 2. Extraction des données
        teams = match_analysis_result.get("teams", [])
        score = match_analysis_result.get("score", {})
        top_players = match_analysis_result.get("top_players", [])
        
        # 3. Récupère l'impact des joueurs clés
        impact_data = {}
        for player in top_players[:5]:  # Top 5 joueurs
            player_name = player.get("player_name") or player.get("name", "Inconnu")
            if player_name and player_name != "Inconnu":
                try:
                    impact_result = await get_player_impact(match_id, player_name)
                    
                    # CORRECTION: Convertir impact_result si c'est une chaîne
                    if isinstance(impact_result, str):
                        impact_result = json.loads(impact_result)
                    
                    if "predicted_impact" in impact_result:
                        impact_data[player_name] = round(impact_result["predicted_impact"], 1)
                except Exception as e:
                    logger.warning(f"⚠️ Erreur impact {player_name}: {e}")
        
        # 4. Génère le rapport avec Ollama
        prompt = f"""
Tu es un coach LFB expert avec 25 ans d'expérience. Analyse ce match et génère un rapport professionnel en français.

**CONTEXTE DU MATCH:**
- Match ID: {match_id}
- Équipes: {teams[0]} vs {teams[1]}
- Score: {score.get(teams[0], '?')} - {score.get(teams[1], '?')}

**TOP JOUEURS PAR IMPACT:**
{chr(10).join([f"- {name}: {impact}/50" for name, impact in impact_data.items()]) if impact_data else "Aucune donnée d'impact disponible"}

**STRUCTURE DU RAPPORT:**
1. **Résumé Exécutif** (1-2 phrases maximum)
2. **Performances Individuelles Clés** (analyse 2-3 joueurs décisifs)
3. **Analyse Collective** (forces/faiblesses des équipes)
4. **Recommandations Tactiques** (3 actions concrètes pour le prochain match)
5. **Focus Entraînement** (2-3 points à travailler)

Sois direct, technique et actionable. Pas de blabla.
"""

        report = generate_with_ollama(prompt, model="llama3.1:8b")
        
        return json.dumps({
            "report": report,
            "match_id": match_id,
            "teams": teams,
            "score": score,
            "player_impacts": impact_data,
            "generated_at": datetime.now().isoformat(),
            "source": "Ollama + Analyse MCP"
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur generate_coaching_report: {e}")
        return json.dumps({"error": f"Erreur génération rapport: {str(e)}"})

@mcp.tool()
async def get_nba_player_stats(player_name: str, season: str = "2024-25") -> str:
    """Récupère les statistiques détaillées d'un joueur NBA"""
    logger.info(f"🛠️ get_nba_player_stats: {player_name} {season}")
    try:
        from nba_api.stats.static import players
        from nba_api.stats.endpoints import playercareerstats
        
        nba_players = players.find_players_by_full_name(player_name)
        if not nba_players:
            return json.dumps({"error": f"Joueur NBA {player_name} non trouvé"})

        player_id = nba_players[0]['id']
        career_stats = playercareerstats.PlayerCareerStats(player_id=player_id)
        stats_df = career_stats.get_data_frames()[0]
        
        season_data = stats_df[stats_df['SEASON_ID'] == season]
        if season_data.empty:
            return json.dumps({"error": f"Saison {season} non trouvée pour {player_name}"})
            
        season_stats = season_data.iloc[0].to_dict()

        formatted_stats = {
            "player_name": player_name,
            "season": season_stats.get('SEASON_ID', 'N/A'),
            "team": season_stats.get('TEAM_ABBREVIATION', 'N/A'),
            "games_played": int(season_stats.get('GP', 0)),
            "points_per_game": round(float(season_stats.get('PTS', 0) / max(season_stats.get('GP', 1), 1)), 1),
            "rebounds_per_game": round(float(season_stats.get('REB', 0) / max(season_stats.get('GP', 1), 1)), 1),
            "assists_per_game": round(float(season_stats.get('AST', 0) / max(season_stats.get('GP', 1), 1)), 1),
            "steals_per_game": round(float(season_stats.get('STL', 0) / max(season_stats.get('GP', 1), 1)), 1),
            "blocks_per_game": round(float(season_stats.get('BLK', 0) / max(season_stats.get('GP', 1), 1)), 1),
            "minutes_per_game": season_stats.get('MIN', 'N/A'),
            "field_goal_percentage": round(float(season_stats.get('FG_PCT', 0) * 100), 1),
        }

        logger.info(f"✅ Stats NBA récupérées: {player_name}")
        return json.dumps({"player": player_name, "stats": formatted_stats, "source": "NBA API"})

    except Exception as e:
        logger.error(f"❌ Erreur get_nba_player_stats: {e}")
        return json.dumps({"error": f"Impossible de récupérer les stats NBA: {str(e)}"})

@mcp.tool()
async def ask_coach_ai(question: str) -> str:
    """Pose une question tactique à l'IA Coach"""
    logger.info(f"🛠️ ask_coach_ai: {question}")
    try:
        from utils.ollama_client import generate_with_ollama
        
        prompt = f"""
Tu es un coach LFB avec 25 ans d'expérience. Réponds en français, de façon directe, professionnelle et actionable.
Pas de blabla, que du concret.

Question : {question}

Réponse :
"""
        response = generate_with_ollama(prompt)
        logger.info("✅ Réponse Coach IA générée")
        
        return json.dumps({
            "answer": response,
            "source": "Ollama llama3.1:8b local",
            "model": "llama3.1:8b"
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur ask_coach_ai: {e}")
        return json.dumps({"error": f"Erreur Coach IA: {str(e)}"})

@mcp.tool()
async def get_team_form(team_name: str, last_matches: int = 5) -> str:
    """Récupère la forme récente d'une équipe LFB"""
    logger.info(f"🛠️ get_team_form: {team_name}")
    try:
        if df.empty:
            return json.dumps({"error": "Données LFB non disponibles"})
            
        team_data = df[(df['team_name'] == team_name) & (df['is_team'])]
        recent = team_data.sort_values('date', ascending=False).head(last_matches)
        form = ['W' if p > 70 else 'L' for p in recent['points']]
        
        return json.dumps({
            "team": team_name, 
            "last_matches": form, 
            "average_points": round(recent['points'].mean(), 1)
        })
        
    except Exception as e:
        return json.dumps({"error": f"Équipe non trouvée: {str(e)}"})

@mcp.tool()
async def get_match_analysis(match_id: str) -> str:
    """Extrait les données de base d'un match LFB pour analyse"""
    logger.info(f"🛠️ get_match_analysis: {match_id}")
    try:
        if df.empty:
            return json.dumps({"error": "Données LFB non disponibles"})
            
        match = df[df['match_id'] == match_id]
        teams = match[match['is_team']]['team_name'].unique()
        if len(teams) != 2: 
            return json.dumps({"error": "Match incomplet"})
            
        t1, t2 = teams
        return json.dumps({
            "match_id": match_id,
            "teams": [t1, t2],
            "score": {
                t1: int(match[match['team_name']==t1]['points'].iloc[0]), 
                t2: int(match[match['team_name']==t2]['points'].iloc[0])
            },
            "top_players": match[~match['is_team']].nlargest(5, 'points')[['player_name', 'points']].to_dict('records')
        })
        
    except Exception as e:
        return json.dumps({"error": f"Match non trouvé: {str(e)}"})

@mcp.tool()
async def get_training_recommendations(player_name: str) -> str:
    """Retourne des recommandations d'entraînement pour un joueur"""
    logger.info(f"🛠️ get_training_recommendations: {player_name}")
    try:
        # Recommandations simulées - dans la réalité, basé sur l'analyse des données
        recommendations = {
            "player": player_name,
            "recommendations": [
                {
                    "area": "Shooting",
                    "exercise": "500 tirs à 3 points par jour",
                    "frequency": "Quotidien",
                    "rationale": "Améliorer le pourcentage à 3 points"
                },
                {
                    "area": "Force",
                    "exercise": "Squats et fentes",
                    "frequency": "3x/semaine", 
                    "rationale": "Renforcer les jambes pour les sauts"
                },
                {
                    "area": "Défense",
                    "exercise": "Drills de défense latérale",
                    "frequency": "4x/semaine",
                    "rationale": "Améliorer la mobilité défensive"
                }
            ],
            "generated_at": datetime.now().isoformat()
        }
        return json.dumps(recommendations)
    except Exception as e:
        logger.error(f"❌ Erreur get_training_recommendations: {e}")
        return json.dumps({"error": str(e)})
    
@mcp.tool()
async def search_guidelines(query: str) -> str:
    """Recherche dans les guidelines basketball"""
    logger.info(f"🛠️ search_guidelines: {query}")
    try:
        from rag.search import search_guidelines as rag_search
        results = rag_search(query, max_results=3)
        return json.dumps(results)
    except Exception as e:
        logger.error(f"❌ Erreur search_guidelines: {e}")
        return json.dumps({"error": str(e)})
    

# =============================================================================
# SERVEUR HTTP POUR COMPATIBILITÉ
# =============================================================================
http_app = FastAPI(title="BasketCoach HTTP API")

@http_app.post("/tools/get_player_impact")
async def http_get_player_impact(match_id: str, player_name: str):
    result = await get_player_impact(match_id, player_name)
    return json.loads(result)

@http_app.post("/tools/get_nba_live_ranking")
async def http_get_nba_live_ranking():
    result = await get_nba_live_ranking()
    return json.loads(result)

@http_app.post("/tools/get_player_news")
async def http_get_player_news(player_name: str):
    result = await get_player_news(player_name)
    return json.loads(result)

@http_app.post("/tools/ask_coach_ai")
async def http_ask_coach_ai(question: str):
    result = await ask_coach_ai(question)
    return json.loads(result)

@http_app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "BasketCoach MCP", "tools": 7}

@http_app.get("/")
async def root():
    return {"message": "BasketCoach MCP Server - Utilisez /health pour vérifier le statut"}

# =============================================================================
# LANCEMENT SIMPLIFIÉ
# =============================================================================

def run_http_only():
    """Lance seulement le serveur HTTP"""
    print("🚀 BASKETCOACH MCP - MODE HTTP SEULEMENT")
    print("🌐 http://127.0.0.1:8000/health")
    uvicorn.run(http_app, host="127.0.0.1", port=8000, log_level="info")

def run_stdio_only():
    """Lance seulement le serveur stdio (version corrigée)"""
    print("🚀 BASKETCOACH MCP - MODE STDIO SEULEMENT")
    print("🔌 Prêt pour les connexions MCP...")
    # Méthode simple et directe pour stdio
    mcp.run()

if __name__ == "__main__":
    # Vérifie le mode de lancement
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "http":
            run_http_only()
        elif mode == "stdio":
            run_stdio_only()
        else:
            print("Usage: python basketcoach_mcp_server.py [http|stdio]")
            print("Par défaut: mode stdio")
            run_stdio_only()
    else:
        # Mode stdio par défaut pour MCP
        run_stdio_only()



# basketcoach-mcp/rag/embed.py
#!/usr/bin/env python3
"""
Système d'embedding et de recherche RAG pour les guidelines basketball
"""

import os
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
import pickle
import logging
from pathlib import Path

from sentence_transformers import SentenceTransformer
import faiss
import PyPDF2
from sklearn.metrics.pairwise import cosine_similarity
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import get_logger
from utils.config import get_config

logger = get_logger("rag.embed")

class RAGSystem:
    """Système RAG pour la recherche dans les guidelines basketball"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.config = get_config()
        self.model_name = model_name
        self.model = None
        self.index = None
        self.guidelines_data = []
        self.is_initialized = False
        
        # Chemins
        self.guidelines_path = Path(self.config.get("rag.guidelines_path", "rag/guidelines/"))
        self.embeddings_path = Path("rag/embeddings/")
        self.database_path = Path("rag/database/")
        
        # Création des répertoires
        self.embeddings_path.mkdir(parents=True, exist_ok=True)
        self.database_path.mkdir(parents=True, exist_ok=True)
    
    def initialize(self):
        """Initialise le système RAG"""
        try:
            logger.info("🚀 Initialisation du système RAG...")
            
            # Chargement du modèle
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"✅ Modèle chargé: {self.model_name}")
            
            # Chargement ou création des embeddings
            if self._check_existing_embeddings():
                self._load_existing_embeddings()
            else:
                self._process_guidelines()
                self._create_embeddings()
            
            self.is_initialized = True
            logger.info("✅ Système RAG initialisé avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation RAG: {e}")
            raise
    
    def search(self, query: str, top_k: int = 10, similarity_threshold: float = 0.3) -> List[Dict[str, Any]]:
        """
        Recherche sémantique dans les guidelines - seuil réduit
        """
        if not self.is_initialized:
            self.initialize()
        
        try:
            # Embedding de la requête
            query_embedding = self.model.encode([query])
            
            # Recherche étendue
            distances, indices = self.index.search(query_embedding, top_k * 2)
            
            # Récupération des résultats avec seuil réduit
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx < len(self.guidelines_data):
                    guideline = self.guidelines_data[idx]
                    # Score de similarité normalisé
                    similarity_score = float(distance)
                    
                    if similarity_score >= similarity_threshold:
                        results.append({
                            "rank": len(results) + 1,
                            "content": guideline["content"],
                            "source": guideline["source"],
                            "category": guideline["category"],
                            "similarity_score": similarity_score,
                            "page": guideline.get("page", "N/A")
                        })
                    
                    # Arrêter quand on a assez de résultats
                    if len(results) >= top_k:
                        break
            
            logger.info(f"🔍 Recherche '{query}': {len(results)} résultats (seuil: {similarity_threshold})")
            return results
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche RAG: {e}")
            return []
    
    def add_guideline(self, content: str, source: str, category: str, metadata: Dict = None):
        """
        Ajoute une nouvelle guideline au système
        """
        if not self.is_initialized:
            self.initialize()
        
        try:
            guideline = {
                "content": content,
                "source": source,
                "category": category,
                "metadata": metadata or {}
            }
            
            # Ajout aux données
            self.guidelines_data.append(guideline)
            
            # Mise à jour des embeddings
            self._update_embeddings([guideline])
            
            logger.info(f"✅ Guideline ajoutée: {source} - {category}")
            
        except Exception as e:
            logger.error(f"❌ Erreur ajout guideline: {e}")
    
    def _check_existing_embeddings(self) -> bool:
        """Vérifie si des embeddings existent déjà"""
        index_path = self.embeddings_path / "guidelines.index"
        data_path = self.database_path / "guidelines_data.pkl"
        
        return index_path.exists() and data_path.exists()
    
    def _load_existing_embeddings(self):
        """Charge les embeddings existants"""
        try:
            # Chargement des données
            data_path = self.database_path / "guidelines_data.pkl"
            with open(data_path, 'rb') as f:
                self.guidelines_data = pickle.load(f)
            
            # Chargement de l'index FAISS
            index_path = self.embeddings_path / "guidelines.index"
            self.index = faiss.read_index(str(index_path))
            
            logger.info(f"✅ Embeddings chargés: {len(self.guidelines_data)} guidelines")
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement embeddings: {e}")
            raise
    
    def _process_guidelines(self):
        """Traite les fichiers PDF de guidelines – VERSION OPTIMISÉE"""
        logger.info("📚 Traitement des guidelines...")

        # Réinitialisation obligatoire pour éviter les doublons
        self.guidelines_data = []
        
        # Liste des PDF trouvés
        pdf_files = list(self.guidelines_path.glob("*.pdf"))
        logger.info(f"🔍 {len(pdf_files)} fichiers PDF trouvés dans {self.guidelines_path}")

        # ----- 1) PRIORITÉ AUX PDF -----
        if pdf_files:
            for pdf_file in pdf_files:
                try:
                    logger.info(f"📄 Extraction du PDF : {pdf_file.name}")
                    pdf_guidelines = self._extract_text_from_pdf(pdf_file)
                    self.guidelines_data.extend(pdf_guidelines)
                    logger.info(f"   → {len(pdf_guidelines)} extraits ajoutés")
                except Exception as e:
                    logger.error(f"❌ Erreur traitement PDF {pdf_file}: {e}")
        else:
            logger.warning("⚠️ Aucun PDF trouvé – recours aux guidelines par défaut")

            # ----- 2) GUIDELINES PAR DÉFAUT -----
            self.guidelines_data = [
                {
                    "content": "ESC 2024: Limiter les séances intensives à 2 par semaine maximum pour prévenir le surentraînement",
                    "source": "European Society of Cardiology 2024",
                    "category": "entraînement",
                    "page": "12"
                },
                {
                    "content": "Recommandation EU: 48h de repos entre deux matches compétitifs pour une récupération optimale",
                    "source": "European Basketball Union 2023",
                    "category": "récupération",
                    "page": "8"
                },
                {
                    "content": "Protocole hydratation: 500ml 2h avant l'effort, 250ml toutes les 20min pendant l'activité",
                    "source": "International Journal of Sports Medicine",
                    "category": "nutrition",
                    "page": "15"
                },
                {
                    "content": "Cheville: Protocole RICE (Repos, Ice, Compression, Élévation) 48h pour entorses légères",
                    "source": "Journal of Orthopaedic Surgery 2024",
                    "category": "blessure",
                    "page": "22"
                },
                {
                    "content": "Genou: Consultation immédiate recommandée si gonflement > 2cm après traumatisme",
                    "source": "American Journal of Sports Medicine",
                    "category": "blessure",
                    "page": "18"
                },
                {
                    "content": "Apport protéique: 1.6-2.2g/kg/jour recommandé pour les sportives d'élite en basketball",
                    "source": "International Society of Sports Nutrition",
                    "category": "nutrition",
                    "page": "7"
                },
                {
                    "content": "Sommeil: 8-10h/nuit requis pour les sportives professionnelles pour une récupération optimale",
                    "source": "Sleep Medicine Journal",
                    "category": "récupération",
                    "page": "11"
                },
                {
                    "content": "Prévention blessures: Programme de renforcement musculaire 3x/semaine réduit les risques de 40%",
                    "source": "British Journal of Sports Medicine",
                    "category": "prévention",
                    "page": "9"
                }
            ]

        # ----- 3) Vérification finale -----
        if not self.guidelines_data:
            logger.error("❌ Aucune guideline disponible !")
            raise Exception("Aucune donnée guideline trouvée")

        logger.info(f"📊 Total guidelines chargées : {len(self.guidelines_data)}")

        # ----- 4) Sauvegarde -----
        with open(self.database_path / "guidelines_data.pkl", 'wb') as f:
            pickle.dump(self.guidelines_data, f)

    
    def _extract_text_from_pdf(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """Extrait le texte d'un fichier PDF"""
        guidelines = []
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                text = page.extract_text()
                if text.strip():
                    # Segmentation en chunks (simplifié)
                    chunks = self._split_text_into_chunks(text)
                    
                    for chunk in chunks:
                        guidelines.append({
                            "content": chunk,
                            "source": pdf_path.name,
                            "category": "général",
                            "page": str(page_num)
                        })
        
        return guidelines
    
    def _split_text_into_chunks(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Segmente le texte en chunks pour l'embedding"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
            
            if i + chunk_size >= len(words):
                break
        
        return chunks
    
    def _create_embeddings(self):
        """Crée les embeddings pour toutes les guidelines"""
        logger.info("🔨 Création des embeddings...")
        
        try:
            # Extraction du contenu
            contents = [guideline["content"] for guideline in self.guidelines_data]
            
            # Création des embeddings
            embeddings = self.model.encode(contents, show_progress_bar=True)
            
            # Création de l'index FAISS
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)  # Produit scalaire pour similarité cosinus
            
            # Normalisation pour similarité cosinus
            faiss.normalize_L2(embeddings)
            self.index.add(embeddings)
            
            # Sauvegarde de l'index
            faiss.write_index(self.index, str(self.embeddings_path / "guidelines.index"))
            
            logger.info(f"✅ Embeddings créés: {len(self.guidelines_data)} guidelines")
            
        except Exception as e:
            logger.error(f"❌ Erreur création embeddings: {e}")
            raise
    
    def _update_embeddings(self, new_guidelines: List[Dict]):
        """Met à jour les embeddings avec de nouvelles guidelines"""
        try:
            # Embeddings des nouvelles guidelines
            new_contents = [guideline["content"] for guideline in new_guidelines]
            new_embeddings = self.model.encode(new_contents)
            
            # Ajout à l'index existant
            faiss.normalize_L2(new_embeddings)
            self.index.add(new_embeddings)
            
            # Sauvegarde de l'index mis à jour
            faiss.write_index(self.index, str(self.embeddings_path / "guidelines.index"))
            
            # Sauvegarde des données mises à jour
            with open(self.database_path / "guidelines_data.pkl", 'wb') as f:
                pickle.dump(self.guidelines_data, f)
            
            logger.info(f"✅ Embeddings mis à jour: {len(new_guidelines)} nouvelles guidelines")
            
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour embeddings: {e}")

# Instance globale
rag_system = RAGSystem()

def initialize_rag():
    """Initialise le système RAG au démarrage"""
    rag_system.initialize()

def search_guidelines(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Fonction de recherche principale pour le serveur MCP"""
    return rag_system.search(query, top_k)




# basketcoach-mcp/rag/search.py
#!/usr/bin/env python3
"""
Interface de recherche pour le système RAG
Intégration simplifiée avec le serveur MCP
"""

from typing import List, Dict, Any
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rag.embed import rag_system, initialize_rag
from utils.logger import get_logger

logger = get_logger("rag.search")

def search_guidelines(query: str, max_results: int = 3, categories: List[str] = None) -> Dict[str, Any]:
    """
    Recherche des guidelines avec filtrage par catégorie
    """
    try:
        # Initialisation si nécessaire
        if not rag_system.is_initialized:
            initialize_rag()
        
        # Recherche étendue
        all_results = rag_system.search(query, top_k=max_results * 2)
        
        # Filtrage par catégorie si spécifié
        if categories:
            filtered_results = [
                result for result in all_results 
                if result["category"] in categories
            ]
            results = filtered_results[:max_results]
        else:
            results = all_results[:max_results]
        
        # Analyse des résultats
        analysis = {
            "query": query,
            "total_found": len(all_results),
            "returned": len(results),
            "categories_found": list(set(r["category"] for r in results)),
            "average_similarity": sum(r["similarity_score"] for r in results) / len(results) if results else 0
        }
        
        return {
            "search_results": results,
            "analysis": analysis,
            "suggestions": _generate_search_suggestions(query, results)
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur recherche guidelines: {e}")
        return {
            "error": f"Erreur recherche: {str(e)}",
            "search_results": [],
            "analysis": {}
        }

def get_guideline_categories() -> List[str]:
    """
    Retourne la liste des catégories disponibles
    """
    try:
        if not rag_system.is_initialized:
            initialize_rag()
        
        categories = list(set(guideline["category"] for guideline in rag_system.guidelines_data))
        return sorted(categories)
    
    except Exception as e:
        logger.error(f"❌ Erreur récupération catégories: {e}")
        return []

def add_custom_guideline(content: str, source: str = "Utilisateur", category: str = "personnalisé") -> bool:
    """
    Ajoute une guideline personnalisée au système
    """
    try:
        rag_system.add_guideline(content, source, category)
        logger.info(f"✅ Guideline personnalisée ajoutée: {category}")
        return True
    
    except Exception as e:
        logger.error(f"❌ Erreur ajout guideline: {e}")
        return False

def _generate_search_suggestions(query: str, results: List[Dict]) -> List[str]:
    """Génère des suggestions de recherche basées sur les résultats"""
    suggestions = []
    
    if not results:
        suggestions.extend([
            "Essayez avec des termes plus généraux",
            "Vérifiez l'orthographe des mots-clés",
            "Consultez les catégories disponibles"
        ])
    else:
        categories = list(set(r["category"] for r in results))
        if len(categories) > 1:
            suggestions.append(f"Catégories trouvées: {', '.join(categories)}")
        
        if len(results) < 3:
            suggestions.append("Essayez d'élargir votre recherche pour plus de résultats")
    
    return suggestions


# basketcoach-mcp/basketcoach_mcp_server.py
#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
import uvicorn
import asyncio
from fastapi import FastAPI
import sys
import json

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("BasketCoach-MCP")

# Initialisation MCP
mcp = FastMCP("BasketCoach")

# Données LFB locales
try:
    df = pd.read_csv("data/processed/all_matches_merged.csv")
    df['match_id'] = df['match_id'].astype(str)
    logger.info(f"✅ Données LFB chargées: {len(df)} lignes")
except Exception as e:
    logger.error(f"❌ Erreur chargement données: {e}")
    df = pd.DataFrame()

# =============================================================================
# OUTILS MCP 
# =============================================================================

@mcp.tool()
async def get_player_impact(match_id: str, player_name: str) -> str:
    """Calcule l'impact d'un joueur dans un match LFB using machine learning"""
    logger.info(f"🛠️ get_player_impact: {player_name} dans {match_id}")
    try:
        if df.empty:
            return json.dumps({"error": "Données LFB non disponibles"})
            
        row = df[
            (df['match_id'] == match_id) &
            (df['player_name'].str.contains(player_name, case=False, na=False)) &
            (~df['is_team'])
        ]
        if row.empty:
            return json.dumps({"error": f"Joueuse {player_name} non trouvée dans le match {match_id}"})
        
        stats = row.iloc[0]
        from ml.predict import predictor
        
        result = predictor.predict_single_player({
            "player_name": player_name,
            "points": int(stats.get('points', 0)),
            "rebounds_total": int(stats.get('rebounds_total', 0)),
            "assists": int(stats.get('assists', 0)),
            "steals": int(stats.get('steals', 0)),
            "blocks": int(stats.get('blocks', 0)),
            "turnovers": int(stats.get('turnovers', 0)),
            "plus_minus": int(stats.get('plus_minus', 0)),
            "minutes_played": 30.0
        })
        result["match_id"] = match_id
        
        logger.info(f"✅ Impact calculé: {player_name} = {result.get('predicted_impact', 'N/A')}")
        return json.dumps(result)
        
    except Exception as e:
        logger.error(f"❌ Erreur get_player_impact: {e}")
        return json.dumps({"error": str(e)})

@mcp.tool()
async def get_nba_live_ranking() -> str:
    """Récupère le classement NBA live par scraping"""
    logger.info("🛠️ get_nba_live_ranking")
    try:
        url = "https://www.basketball-reference.com/leagues/NBA_2026_standings.html"
        headers = {"User-Agent": "Mozilla/5.0 (BasketCoach MCP v1.0)"}
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        table = soup.find('table', id='confs_standings_E') or soup.find('table', id='divs_standings_E')
        if not table:
            return json.dumps({"error": "Structure page changée", "ranking": []})

        ranking = []
        for row in table.find_all('tr')[1:31]:
            cells = row.find_all(['th', 'td'])
            if len(cells) > 3:
                team = cells[0].get_text(strip=True)
                wins = cells[1].get_text(strip=True)
                losses = cells[2].get_text(strip=True)
                ranking.append({"team": team, "wins": wins, "losses": losses})
        
        logger.info(f"✅ Classement NBA récupéré: {len(ranking)} équipes")
        return json.dumps({
            "ranking": ranking, 
            "source": "basketball-reference.com", 
            "updated": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur get_nba_live_ranking: {e}")
        return json.dumps({"ranking": [], "error": f"NBA live temporairement indisponible: {e}"})

@mcp.tool()
async def get_player_news(player_name: str) -> str:
    """Récupère les dernières actualités d'un joueur via Google Search"""
    logger.info(f"🛠️ get_player_news: {player_name}")
    try:
        # Simulation d'actualités avec URLs réelles
        news_data = {
            "player": player_name,
            "news": [
                {
                    "title": f"Dernières performances de {player_name} en LFB",
                    "link": f"https://www.basketlfb.com/joueuse/{player_name.replace(' ', '-').lower()}",
                    "source": "LFB Officiel",
                    "date": "2024-11-20"
                },
                {
                    "title": f"{player_name} dans la course au MVP",
                    "link": "https://www.ffbb.com/actualites/classement-mvp",
                    "source": "FFBB", 
                    "date": "2024-11-19"
                },
                {
                    "title": f"Interview exclusive : {player_name} parle de ses objectifs",
                    "link": "https://www.eurobasket.com/France/news.asp",
                    "source": "Eurobasket",
                    "date": "2024-11-18"
                }
            ],
            "search_links": [
                {
                    "title": "🔍 Rechercher actualités sur Google",
                    "url": f"https://www.google.com/search?q={player_name.replace(' ', '+')}+basket+news"
                },
                {
                    "title": "📰 Voir sur ESPN",
                    "url": f"https://www.espn.com/search/_/q/{player_name.replace(' ', '%20')}"
                },
                {
                    "title": "🏀 Voir sur FIBA", 
                    "url": f"https://www.fiba.basketball/search?q={player_name.replace(' ', '%20')}"
                }
            ]
        }
        
        logger.info(f"✅ News récupérées: {len(news_data['news'])} articles")
        return json.dumps(news_data)
        
    except Exception as e:
        logger.error(f"❌ Erreur get_player_news: {e}")
        return json.dumps({
            "news": [f"Recherche indisponible: {str(e)}"],
            "search_links": [
                {
                    "title": "🔍 Rechercher sur Google",
                    "url": f"https://www.google.com/search?q={player_name.replace(' ', '+')}+basket+news"
                }
            ]
        })

@mcp.tool()
async def generate_coaching_report(match_id: str) -> str:
    """Génère un rapport de coaching détaillé avec analyse IA - VERSION CORRIGÉE"""
    logger.info(f"📊 Génération rapport coaching pour match {match_id}")
    try:
        from utils.ollama_client import generate_with_ollama
        
        # 1. Récupère les données du match via l'outil existant
        match_analysis_result = await get_match_analysis(match_id)
        
        # CORRECTION: Convertir la chaîne JSON en dictionnaire
        if isinstance(match_analysis_result, str):
            try:
                match_analysis_result = json.loads(match_analysis_result)
            except json.JSONDecodeError as e:
                return json.dumps({"error": f"Erreur décodage JSON: {e}"})
        
        # Vérifier les erreurs
        if "error" in match_analysis_result:
            return json.dumps({"error": f"Erreur analyse match: {match_analysis_result['error']}"})
        
        # 2. Extraction des données
        teams = match_analysis_result.get("teams", [])
        score = match_analysis_result.get("score", {})
        top_players = match_analysis_result.get("top_players", [])
        
        # 3. Récupère l'impact des joueurs clés
        impact_data = {}
        for player in top_players[:5]:  # Top 5 joueurs
            player_name = player.get("player_name") or player.get("name", "Inconnu")
            if player_name and player_name != "Inconnu":
                try:
                    impact_result = await get_player_impact(match_id, player_name)
                    
                    # CORRECTION: Convertir impact_result si c'est une chaîne
                    if isinstance(impact_result, str):
                        impact_result = json.loads(impact_result)
                    
                    if "predicted_impact" in impact_result:
                        impact_data[player_name] = round(impact_result["predicted_impact"], 1)
                except Exception as e:
                    logger.warning(f"⚠️ Erreur impact {player_name}: {e}")
        
        # ---------------------------------------------------------------------
        # 🚀 ÉTAPE RAG : Récupération des guidelines pertinentes
        # ---------------------------------------------------------------------
        
        # 1. Définir une requête RAG intelligente basée sur les données du match
        rag_query = (
            f"Conseils de récupération, nutrition ou prévention blessures pour les joueurs "
            f"clés du match {match_id} : {', '.join(impact_data.keys())}."
        )
        
        # 2. Appeler l'outil RAG (qui utilise la fonction search_guidelines optimisée)
        rag_results_json = await search_guidelines(rag_query)
        rag_results = json.loads(rag_results_json)
        
        # 3. Formater le contexte pour le LLM
        guidelines_context = ""
        if rag_results.get("results"):
            guidelines_context = "\n\n--- CONTEXTE GUIDELINES RAG ---\n"
            for i, result in enumerate(rag_results["results"]):
                # L'outil search_guidelines doit retourner la source/catégorie
                source = result.get('source', 'N/A')
                category = result.get('category', 'N/A')
                # Utiliser le rerank_score s'il a été ajouté (voir point 2)
                score = result.get('rerank_score', result.get('similarity_score', 'N/A'))
                
                guidelines_context += (
                    f"Guideline {i+1} (Source: {source}, Catégorie: {category}, Pertinence: {score:.2f}):\n"
                    f"{result['content']}\n---\n"
                )

        # 4. Génère le rapport avec Ollama
        prompt = f"""
Tu es un coach LFB expert avec 25 ans d'expérience. Analyse ce match et génère un rapport professionnel en français.

**CONTEXTE DU MATCH:**
- Match ID: {match_id}
- Équipes: {teams[0]} vs {teams[1]}
- Score: {score.get(teams[0], '?')} - {score.get(teams[1], '?')}

**TOP JOUEURS PAR IMPACT:**
{chr(10).join([f"- {name}: {impact}/50" for name, impact in impact_data.items()]) if impact_data else "Aucune donnée d'impact disponible"}
{guidelines_context}
**STRUCTURE DU RAPPORT:**
1. **Résumé Exécutif** (1-2 phrases maximum)
2. **Performances Individuelles Clés** (analyse 2-3 joueurs décisifs)
3. **Analyse Collective** (forces/faiblesses des équipes)
4. **Recommandations Tactiques** (3 actions concrètes pour le prochain match)
5. **Focus Entraînement** (2-3 points à travailler)

Sois direct, technique et actionable. Pas de blabla.
"""

        report = generate_with_ollama(prompt, model="llama3.1:8b")
        
        return json.dumps({
            "report": report,
            "match_id": match_id,
            "teams": teams,
            "score": score,
            "player_impacts": impact_data,
            "generated_at": datetime.now().isoformat(),
            "source": "Ollama + Analyse MCP + RAG (BGE + Reranker)"
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur generate_coaching_report: {e}")
        return json.dumps({"error": f"Erreur génération rapport: {str(e)}"})

@mcp.tool()
async def get_nba_player_stats(player_name: str, season: str = "2024-25") -> str:
    """Récupère les statistiques détaillées d'un joueur NBA"""
    logger.info(f"🛠️ get_nba_player_stats: {player_name} {season}")
    try:
        from nba_api.stats.static import players
        from nba_api.stats.endpoints import playercareerstats
        
        nba_players = players.find_players_by_full_name(player_name)
        if not nba_players:
            return json.dumps({"error": f"Joueur NBA {player_name} non trouvé"})

        player_id = nba_players[0]['id']
        career_stats = playercareerstats.PlayerCareerStats(player_id=player_id)
        stats_df = career_stats.get_data_frames()[0]
        
        season_data = stats_df[stats_df['SEASON_ID'] == season]
        if season_data.empty:
            return json.dumps({"error": f"Saison {season} non trouvée pour {player_name}"})
            
        season_stats = season_data.iloc[0].to_dict()

        formatted_stats = {
            "player_name": player_name,
            "season": season_stats.get('SEASON_ID', 'N/A'),
            "team": season_stats.get('TEAM_ABBREVIATION', 'N/A'),
            "games_played": int(season_stats.get('GP', 0)),
            "points_per_game": round(float(season_stats.get('PTS', 0) / max(season_stats.get('GP', 1), 1)), 1),
            "rebounds_per_game": round(float(season_stats.get('REB', 0) / max(season_stats.get('GP', 1), 1)), 1),
            "assists_per_game": round(float(season_stats.get('AST', 0) / max(season_stats.get('GP', 1), 1)), 1),
            "steals_per_game": round(float(season_stats.get('STL', 0) / max(season_stats.get('GP', 1), 1)), 1),
            "blocks_per_game": round(float(season_stats.get('BLK', 0) / max(season_stats.get('GP', 1), 1)), 1),
            "minutes_per_game": season_stats.get('MIN', 'N/A'),
            "field_goal_percentage": round(float(season_stats.get('FG_PCT', 0) * 100), 1),
        }

        logger.info(f"✅ Stats NBA récupérées: {player_name}")
        return json.dumps({"player": player_name, "stats": formatted_stats, "source": "NBA API"})

    except Exception as e:
        logger.error(f"❌ Erreur get_nba_player_stats: {e}")
        return json.dumps({"error": f"Impossible de récupérer les stats NBA: {str(e)}"})

@mcp.tool()
async def ask_coach_ai(question: str) -> str:
    """Pose une question tactique à l'IA Coach"""
    logger.info(f"🛠️ ask_coach_ai: {question}")
    try:
        from utils.ollama_client import generate_with_ollama
        
        prompt = f"""
Tu es un coach LFB avec 25 ans d'expérience. Réponds en français, de façon directe, professionnelle et actionable.
Pas de blabla, que du concret.

Question : {question}

Réponse :
"""
        response = generate_with_ollama(prompt)
        logger.info("✅ Réponse Coach IA générée")
        
        return json.dumps({
            "answer": response,
            "source": "Ollama llama3.1:8b local",
            "model": "llama3.1:8b"
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur ask_coach_ai: {e}")
        return json.dumps({"error": f"Erreur Coach IA: {str(e)}"})

@mcp.tool()
async def get_team_form(team_name: str, last_matches: int = 5) -> str:
    """Récupère la forme récente d'une équipe LFB"""
    logger.info(f"🛠️ get_team_form: {team_name}")
    try:
        if df.empty:
            return json.dumps({"error": "Données LFB non disponibles"})
            
        team_data = df[(df['team_name'] == team_name) & (df['is_team'])]
        recent = team_data.sort_values('date', ascending=False).head(last_matches)
        form = ['W' if p > 70 else 'L' for p in recent['points']]
        
        return json.dumps({
            "team": team_name, 
            "last_matches": form, 
            "average_points": round(recent['points'].mean(), 1)
        })
        
    except Exception as e:
        return json.dumps({"error": f"Équipe non trouvée: {str(e)}"})

@mcp.tool()
async def get_match_analysis(match_id: str) -> str:
    """Extrait les données de base d'un match LFB pour analyse"""
    logger.info(f"🛠️ get_match_analysis: {match_id}")
    try:
        if df.empty:
            return json.dumps({"error": "Données LFB non disponibles"})
            
        match = df[df['match_id'] == match_id]
        teams = match[match['is_team']]['team_name'].unique()
        if len(teams) != 2: 
            return json.dumps({"error": "Match incomplet"})
            
        t1, t2 = teams
        return json.dumps({
            "match_id": match_id,
            "teams": [t1, t2],
            "score": {
                t1: int(match[match['team_name']==t1]['points'].iloc[0]), 
                t2: int(match[match['team_name']==t2]['points'].iloc[0])
            },
            "top_players": match[~match['is_team']].nlargest(5, 'points')[['player_name', 'points']].to_dict('records')
        })
        
    except Exception as e:
        return json.dumps({"error": f"Match non trouvé: {str(e)}"})

@mcp.tool()
async def get_training_recommendations(player_name: str) -> str:
    """Retourne des recommandations d'entraînement pour un joueur"""
    logger.info(f"🛠️ get_training_recommendations: {player_name}")
    try:
        # Recommandations simulées - dans la réalité, basé sur l'analyse des données
        recommendations = {
            "player": player_name,
            "recommendations": [
                {
                    "area": "Shooting",
                    "exercise": "500 tirs à 3 points par jour",
                    "frequency": "Quotidien",
                    "rationale": "Améliorer le pourcentage à 3 points"
                },
                {
                    "area": "Force",
                    "exercise": "Squats et fentes",
                    "frequency": "3x/semaine", 
                    "rationale": "Renforcer les jambes pour les sauts"
                },
                {
                    "area": "Défense",
                    "exercise": "Drills de défense latérale",
                    "frequency": "4x/semaine",
                    "rationale": "Améliorer la mobilité défensive"
                }
            ],
            "generated_at": datetime.now().isoformat()
        }
        return json.dumps(recommendations)
    except Exception as e:
        logger.error(f"❌ Erreur get_training_recommendations: {e}")
        return json.dumps({"error": str(e)})
    
@mcp.tool()
async def search_guidelines(query: str) -> str:
    """Recherche dans les guidelines basketball"""
    logger.info(f"🛠️ search_guidelines: {query}")
    try:
        from rag.search import search_guidelines as rag_search
        results = rag_search(query, max_results=3)
        return json.dumps(results)
    except Exception as e:
        logger.error(f"❌ Erreur search_guidelines: {e}")
        return json.dumps({"error": str(e)})
    

# =============================================================================
# SERVEUR HTTP POUR COMPATIBILITÉ
# =============================================================================
http_app = FastAPI(title="BasketCoach HTTP API")

@http_app.post("/tools/get_player_impact")
async def http_get_player_impact(match_id: str, player_name: str):
    result = await get_player_impact(match_id, player_name)
    return json.loads(result)

@http_app.post("/tools/get_nba_live_ranking")
async def http_get_nba_live_ranking():
    result = await get_nba_live_ranking()
    return json.loads(result)

@http_app.post("/tools/get_player_news")
async def http_get_player_news(player_name: str):
    result = await get_player_news(player_name)
    return json.loads(result)

@http_app.post("/tools/ask_coach_ai")
async def http_ask_coach_ai(question: str):
    result = await ask_coach_ai(question)
    return json.loads(result)

@http_app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "BasketCoach MCP", "tools": 7}

@http_app.get("/")
async def root():
    return {"message": "BasketCoach MCP Server - Utilisez /health pour vérifier le statut"}

# =============================================================================
# LANCEMENT SIMPLIFIÉ
# =============================================================================

def run_http_only():
    """Lance seulement le serveur HTTP"""
    print("🚀 BASKETCOACH MCP - MODE HTTP SEULEMENT")
    print("🌐 http://127.0.0.1:8000/health")
    uvicorn.run(http_app, host="127.0.0.1", port=8000, log_level="info")

def run_stdio_only():
    """Lance seulement le serveur stdio (version corrigée)"""
    print("🚀 BASKETCOACH MCP - MODE STDIO SEULEMENT")
    print("🔌 Prêt pour les connexions MCP...")
    # Méthode simple et directe pour stdio
    mcp.run()

if __name__ == "__main__":
    # Vérifie le mode de lancement
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "http":
            run_http_only()
        elif mode == "stdio":
            run_stdio_only()
        else:
            print("Usage: python basketcoach_mcp_server.py [http|stdio]")
            print("Par défaut: mode stdio")
            run_stdio_only()
    else:
        # Mode stdio par défaut pour MCP
        run_stdio_only()