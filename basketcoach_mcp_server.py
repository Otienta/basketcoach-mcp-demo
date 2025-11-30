# basketcoach-mcp/basketcoach_mcp_server.py
#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
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

# basketcoach-mcp/basketcoach_mcp_server.py
# Remplacez la fonction get_player_news par cette version améliorée :

@mcp.tool()
async def get_player_news(player_name: str) -> str:
    """Récupère les dernières actualités d'un joueur - VERSION AVEC VRAI SCRAPING"""
    logger.info(f"🛠️ get_player_news: {player_name}")
    try:
        # Tentative de scraping d'actualités réelles
        actual_news = await _scrape_real_news(player_name)
        player_stats = await _scrape_player_stats(player_name)
        
        news_data = {
            "player": player_name,
            "news": actual_news if actual_news else await _get_fallback_news(player_name),
            "player_stats": player_stats,
            "search_links": [
                {
                    "title": "🔍 Rechercher actualités sur Google",
                    "url": f"https://www.google.com/search?q={player_name.replace(' ', '+')}+basket+news+2024"
                },
                {
                    "title": "📰 Voir sur ESPN",
                    "url": f"https://www.espn.com/search/_/q/{player_name.replace(' ', '%20')}"
                },
                {
                    "title": "🏀 Voir sur FIBA", 
                    "url": f"https://www.fiba.basketball/search?q={player_name.replace(' ', '%20')}"
                },
                {
                    "title": "🇫🇷 LFB Officiel",
                    "url": "https://basketlfb.com/category/actualites/"
                }
            ],
            "source": "scraping_réel" if actual_news else "fallback_amélioré"
        }
        
        logger.info(f"✅ News récupérées: {len(news_data['news'])} articles, stats: {'oui' if player_stats else 'non'}")
        return json.dumps(news_data)
        
    except Exception as e:
        logger.error(f"❌ Erreur get_player_news: {e}")
        return json.dumps({
            "player": player_name,
            "news": await _get_fallback_news(player_name),
            "player_stats": {"error": "Données temporairement indisponibles"},
            "search_links": [
                {
                    "title": "🔍 Recherche Google",
                    "url": f"https://www.google.com/search?q={player_name.replace(' ', '+')}+basketball+actualités"
                }
            ],
            "error": f"Sources temporairement indisponibles: {str(e)}"
        })

async def _scrape_real_news(player_name: str) -> List[Dict]:
    """Tente de scraper des actualités réelles - version améliorée"""
    try:
        # Sites fiables pour le basket français
        search_urls = [
            f"https://basketlfb.com/?s={player_name.replace(' ', '+')}",
            f"https://www.ffbb.com/search?search={player_name.replace(' ', '+')}",
            f"https://www.eurosport.fr/search/{player_name.replace(' ', '%20')}/",
        ]
        
        news_items = []
        
        for url in search_urls:
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "fr-FR,fr;q=0.8,en-US;q=0.5,en;q=0.3",
                    "Accept-Encoding": "gzip, deflate, br",
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                }
                
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Recherche d'articles selon différents patterns
                articles = []
                articles.extend(soup.find_all('article'))
                articles.extend(soup.find_all('div', class_=['article', 'news-item', 'post', 'actualite']))
                articles.extend(soup.find_all('a', class_=['news-link', 'article-link']))
                
                for article in articles[:5]:  # Limiter à 5 articles par site
                    title = None
                    link = None
                    description = None
                    
                    # Extraire le titre
                    title_elem = article.find(['h1', 'h2', 'h3', 'h4', 'h5'])
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                    
                    # Extraire le lien
                    link_elem = article.find('a', href=True) if article.name != 'a' else article
                    if link_elem and link_elem.get('href'):
                        link = link_elem['href']
                        if link and not link.startswith(('http', '//')):
                            if link.startswith('/'):
                                base_url = '/'.join(url.split('/')[:3])
                                link = base_url + link
                            else:
                                link = url + link
                    
                    # Extraire la description
                    desc_elem = article.find(['p', 'div'], class_=['excerpt', 'description', 'summary'])
                    if desc_elem:
                        description = desc_elem.get_text(strip=True)[:200] + "..."  # Limiter la longueur
                    
                    # Vérifier que nous avons au moins un titre et un lien
                    if title and link and any(keyword.lower() in title.lower() for keyword in [player_name.split()[0], 'basket', 'LFB']):
                        news_items.append({
                            "title": title,
                            "link": link,
                            "source": url.split('/')[2],  # Nom de domaine
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "description": description or f"Article concernant {player_name} trouvé sur {url.split('/')[2]}",
                            "scraped": True
                        })
                        
            except Exception as e:
                logger.debug(f"⚠️ Scraping échoué pour {url}: {e}")
                continue
        
        return news_items[:8]  # Retourner max 8 articles
        
    except Exception as e:
        logger.warning(f"❌ Scraping échoué: {e}")
        return []

async def _scrape_player_stats(player_name: str) -> Dict[str, Any]:
    """Scrape les statistiques du joueur depuis les données LFB disponibles - VERSION CORRIGÉE"""
    try:
        if df.empty:
            return {"error": "Base de données LFB non disponible"}
            
        # Rechercher le joueur dans les données LFB
        player_data = df[
            (df['player_name'].str.contains(player_name, case=False, na=False)) & 
            (~df['is_team'])
        ].copy()  # Utiliser copy() pour éviter les warnings
        
        if player_data.empty:
            return {"error": f"Joueur {player_name} non trouvé dans la base LFB"}
        
        # CORRECTION : Gérer la colonne date qui peut être de type object
        try:
            # Tenter de convertir la colonne date en datetime
            player_data['date_parsed'] = pd.to_datetime(player_data['date'], errors='coerce')
            # Trouver le dernier match valide
            latest_match = player_data.dropna(subset=['date_parsed']).nlargest(1, 'date_parsed')
            dernier_match_date = latest_match['date'].iloc[0] if not latest_match.empty else player_data['date'].iloc[0]
        except Exception as date_error:
            logger.warning(f"⚠️ Erreur conversion date: {date_error}")
            # Fallback: utiliser la première ligne comme dernier match
            dernier_match_date = player_data['date'].iloc[0] if not player_data.empty else "N/A"
        
        # Calculer les statistiques agrégées
        total_games = len(player_data)
        
        # CORRECTION : Vérifier l'existence des colonnes avant de les utiliser
        stats = {
            "nom": player_name,
            "matchs_joues": total_games,
            "dernier_match": dernier_match_date,
            "moyennes": {},
            "meilleures_performances": {},
            "source": "base_donnees_lfb",
            "actualise": datetime.now().isoformat()
        }
        
        # Calculer les moyennes pour chaque colonne disponible
        numeric_columns = ['points', 'rebounds_total', 'assists', 'steals', 'blocks']
        for col in numeric_columns:
            if col in player_data.columns:
                stats["moyennes"][col] = round(player_data[col].mean(), 1)
                stats["meilleures_performances"][f"{col}_max"] = int(player_data[col].max())
        
        # Ajouter l'évaluation si disponible
        if 'evaluation' in player_data.columns:
            stats["moyennes"]["evaluation"] = round(player_data['evaluation'].mean(), 1)
        
        logger.info(f"✅ Statistiques calculées pour {player_name}: {total_games} matchs")
        return stats
        
    except Exception as e:
        logger.error(f"❌ Erreur scraping stats: {e}")
        return {"error": f"Erreur traitement stats: {str(e)}"}

async def _scrape_player_stats(player_name: str) -> Dict[str, Any]:
    """Scrape les statistiques du joueur - VERSION ULTRA ROBUSTE"""
    try:
        if df.empty:
            return {"error": "Base de données LFB non disponible"}
            
        # Rechercher le joueur dans les données LFB
        player_data = df[
            (df['player_name'].str.contains(player_name, case=False, na=False)) & 
            (~df['is_team'])
        ]
        
        if player_data.empty:
            return {"error": f"Joueur {player_name} non trouvé dans la base LFB"}
        
        # CORRECTION : Approche simple sans manipulation de dates
        total_games = len(player_data)
        
        # Calculer les statistiques de base
        stats = {
            "nom": player_name,
            "matchs_joues": total_games,
            "dernier_match": "Voir données brutes",  # Éviter les problèmes de date
            "moyennes": {},
            "meilleures_performances": {},
            "source": "base_donnees_lfb",
            "actualise": datetime.now().isoformat()
        }
        
        # Colonnes numériques à analyser
        numeric_columns = {
            'points': 'Points',
            'rebounds_total': 'Rebonds', 
            'assists': 'Passes',
            'steals': 'Interceptions',
            'blocks': 'Contres'
        }
        
        for col, label in numeric_columns.items():
            if col in player_data.columns:
                # S'assurer que la colonne est numérique
                numeric_series = pd.to_numeric(player_data[col], errors='coerce').dropna()
                if not numeric_series.empty:
                    stats["moyennes"][label.lower()] = round(numeric_series.mean(), 1)
                    stats["meilleures_performances"][f"{label.lower()}_max"] = int(numeric_series.max())
        
        # Statistiques supplémentaires si disponibles
        if 'evaluation' in player_data.columns:
            eval_series = pd.to_numeric(player_data['evaluation'], errors='coerce').dropna()
            if not eval_series.empty:
                stats["moyennes"]["evaluation"] = round(eval_series.mean(), 1)
        
        logger.info(f"✅ Statistiques calculées pour {player_name}: {total_games} matchs, {len(stats['moyennes'])} métriques")
        return stats
        
    except Exception as e:
        logger.error(f"❌ Erreur scraping stats: {e}")
        return {"error": f"Erreur traitement stats: {str(e)}"}

async def _get_fallback_news(player_name: str) -> List[Dict]:
    """Retourne des actualités de fallback améliorées"""
    return [
        {
            "title": f"Performances récentes de {player_name} en LFB",
            "link": f"https://www.google.com/search?q={player_name.replace(' ', '+')}+LFB+2024+stats",
            "source": "Google Sports",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "description": f"Consultez les dernières statistiques et performances de {player_name} dans le championnat LFB.",
            "scraped": False
        },
        {
            "title": f"Analyse technique : {player_name} cette saison",
            "link": f"https://www.youtube.com/results?search_query={player_name.replace(' ', '+')}+basketball+highlights",
            "source": "YouTube Highlights", 
            "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "description": f"Vidéos et analyses des actions marquantes de {player_name}.",
            "scraped": False
        },
        {
            "title": f"{player_name} dans les médias français",
            "link": "https://basketlfb.com/category/actualites/",
            "source": "LFB Actualités",
            "date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
            "description": "Retrouvez toutes les actualités du basket français féminin.",
            "scraped": False
        }
    ]

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