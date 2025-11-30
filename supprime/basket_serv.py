# basketcoach_mcp_server.py – VERSION FINALE 100% MCP STANDARD (comme TechCrunch)
#!/usr/bin/env python3
from fastapi import FastAPI, Body
from typing import Dict, Any
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import uvicorn
import logging
import pandas as pd
from pathlib import Path
from mcp_client import client
app = FastAPI(title="BasketCoach MCP – Standard Officiel")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MCP")

# Données LFB locales
df = pd.read_csv("data/processed/all_matches_merged.csv")
df['match_id'] = df['match_id'].astype(str)

# =============================================================================
# OUTIL 1 – Impact joueur LFB (ML local)
# =============================================================================
@app.post("/tools/get_player_impact")
async def get_player_impact(match_id: str = Body(..., embed=True), player_name: str = Body(..., embed=True)):
    logger.info(f"MCP → get_player_impact: {player_name} dans {match_id}")
    try:
        row = df[
            (df['match_id'] == match_id) &
            (df['player_name'].str.contains(player_name, case=False, na=False)) &
            (~df['is_team'])
        ]
        if row.empty:
            return {"error": f"Joueuse {player_name} non trouvée dans le match {match_id}"}
        stats = row.iloc[0]
        # Ton modèle ML
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
        return result
    except Exception as e:
        return {"error": str(e)}

# =============================================================================
# OUTIL 2 – Classement NBA live (scraping léger comme TechCrunch)
# =============================================================================
@app.post("/tools/get_nba_live_ranking")
async def get_nba_live_ranking():
    try:
        url = "https://www.basketball-reference.com/leagues/NBA_2026_standings.html"
        headers = {"User-Agent": "Mozilla/5.0 (BasketCoach MCP v1.0)"}
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        table = soup.find('table', id='confs_standings_E') or soup.find('table', id='divs_standings_E')
        if not table:
            return {"error": "Structure page changée", "ranking": []}
        
        ranking = []
        for row in table.find_all('tr')[1:31]:
            cells = row.find_all(['th', 'td'])
            if len(cells) > 3:
                team = cells[0].get_text(strip=True)
                wins = cells[1].get_text(strip=True)
                losses = cells[2].get_text(strip=True)
                ranking.append({"team": team, "wins": wins, "losses": losses})
        return {"ranking": ranking, "source": "basketball-reference.com", "updated": datetime.now().isoformat()}
    except:
        return {"ranking": [], "error": "NBA live temporairement indisponible (réseau école)"}

# =============================================================================
# OUTIL 3 – News joueur (scraping Google comme TechCrunch)
# =============================================================================
@app.post("/tools/get_player_news")
async def get_player_news(player_name: str = Body(..., embed=True)):
    logger.info(f"MCP → get_player_news: {player_name}")
    try:
        url = f"https://www.google.com/search?q={player_name}+basket+news&tbs=qdr:w"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, 'html.parser')
        news = []
        for g in soup.find_all('div', class_='g')[:3]:
            a = g.find('a')
            if a:
                title = a.get_text()
                link = a['href']
                news.append({"title": title, "link": link})
        return {"news": news or ["Aucune news récente"]}
    except:
        return {"news": ["Recherche bloquée (normal en salle machine)"]}

# =============================================================================
# OUTIL 5 – Rapport coaching IA (Ollama + MCP)
# =============================================================================
@app.post("/tools/generate_coaching_report")
async def generate_coaching_report(match_id: str = Body(..., embed=True)):
    logger.info(f"MCP → generate_coaching_report pour match {match_id}")
    try:
        from utils.ollama_client import generate_with_ollama
        
        # Récupère les données du match directement depuis le DataFrame
        match_data = df[df['match_id'] == match_id]
        if match_data.empty:
            return {"error": f"Match {match_id} non trouvé"}
            
        teams = match_data[match_data['is_team']]['team_name'].unique()
        if len(teams) != 2:
            return {"error": "Match incomplet"}
            
        t1, t2 = teams
        score = {
            t1: int(match_data[match_data['team_name']==t1]['points'].iloc[0]),
            t2: int(match_data[match_data['team_name']==t2]['points'].iloc[0])
        }
        
        top_players = match_data[~match_data['is_team']].nlargest(5, 'points')[
            ['player_name', 'points']
        ].to_dict('records')
        
        # 3. Impact des joueurs
        impacts = {}
        for player in top_players:
            name = player["player_name"]
            try:
                impact_result = await get_player_impact(match_id, name)
                if "predicted_impact" in impact_result:
                    impacts[name] = impact_result["predicted_impact"]
            except Exception as e:
                logger.warning(f"Impact non calculé pour {name}: {e}")
        
        # 4. Génération du rapport
        prompt = f"""
Tu es un coach LFB avec 25 ans d'expérience. Génère un rapport post-match professionnel en français.

Match : {match_id}
Équipes : {t1} vs {t2}
Score : {score[t1]} - {score[t2]}
Top joueurs : {top_players}
Impacts prédits : {impacts}

Structure du rapport :
1. Résumé du match
2. Performances individuelles clés  
3. Analyse collective
4. Recommandations tactiques
5. Points d'amélioration

Sois direct, précis, et actionable.
"""
        report = generate_with_ollama(prompt)
        return {
            "report": report,
            "match_id": match_id,
            "teams": [t1, t2],
            "score": score,
            "top_players": top_players,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}
# =============================================================================
# OUTIL NBA AVANCÉ – Récupération stats joueur NBA
# =============================================================================
@app.post("/tools/get_nba_player_stats")
async def get_nba_player_stats(player_name: str = Body(..., embed=True), season: str = Body("2024-25")):
    """
    Récupère les statistiques détaillées d'un joueur NBA
    """
    logger.info(f"MCP → get_nba_player_stats: {player_name} {season}")
    try:
        # Utilisation d'une API NBA alternative (plus stable)
        from nba_api.stats.static import players
        from nba_api.stats.endpoints import playercareerstats
        
        # Recherche du joueur
        nba_players = players.find_players_by_full_name(player_name)
        if not nba_players:
            return {"error": f"Joueur NBA {player_name} non trouvé"}
        
        player_id = nba_players[0]['id']
        
        # Récupération des stats carrière
        career_stats = playercareerstats.PlayerCareerStats(player_id=player_id)
        stats_df = career_stats.get_data_frames()[0]
        
        # Filtrage par saison
        if not season:
            season_stats = stats_df.iloc[-1].to_dict()  # Dernière saison
        else:
            season_stats = stats_df[stats_df['SEASON_ID'] == season].iloc[0].to_dict()
        
        # Formatage des statistiques
        formatted_stats = {
            "player_name": player_name,
            "season": season_stats.get('SEASON_ID', 'N/A'),
            "team": season_stats.get('TEAM_ABBREVIATION', 'N/A'),
            "games_played": int(season_stats.get('GP', 0)),
            "points_per_game": float(season_stats.get('PTS', 0) / max(season_stats.get('GP', 1), 1)),
            "rebounds_per_game": float(season_stats.get('REB', 0) / max(season_stats.get('GP', 1), 1)),
            "assists_per_game": float(season_stats.get('AST', 0) / max(season_stats.get('GP', 1), 1)),
            "steals_per_game": float(season_stats.get('STL', 0) / max(season_stats.get('GP', 1), 1)),
            "blocks_per_game": float(season_stats.get('BLK', 0) / max(season_stats.get('GP', 1), 1)),
            "turnovers_per_game": float(season_stats.get('TOV', 0) / max(season_stats.get('GP', 1), 1)),
            "minutes_per_game": season_stats.get('MIN', 'N/A'),
            "field_goal_percentage": float(season_stats.get('FG_PCT', 0) * 100),
        }
        
        return {
            "player": player_name,
            "stats": formatted_stats,
            "source": "NBA API"
        }
        
    except Exception as e:
        logger.error(f"Erreur stats NBA: {e}")
        return {"error": f"Impossible de récupérer les stats NBA: {str(e)}"}

# =============================================================================
# OUTIL NBA – Prédiction d'impact pour joueur NBA
# =============================================================================
@app.post("/tools/get_nba_player_impact")
async def get_nba_player_impact(player_name: str = Body(..., embed=True), season: str = Body("2024-25")):
    """
    Applique le modèle d'impact aux joueurs NBA
    """
    logger.info(f"MCP → get_nba_player_impact: {player_name} {season}")
    try:
        # Récupération des stats NBA
        stats_result = await get_nba_player_stats(player_name, season)
        if "error" in stats_result:
            return stats_result
        
        stats = stats_result["stats"]
        
        # Adaptation des stats NBA au modèle LFB
        from ml.predict import predictor
        
        impact_result = predictor.predict_single_player({
            "player_name": player_name,
            "points": stats["points_per_game"] * 5,  # Adaptation approximative
            "rebounds_total": stats["rebounds_per_game"] * 5,
            "assists": stats["assists_per_game"] * 5,
            "steals": stats["steals_per_game"] * 5,
            "blocks": stats["blocks_per_game"] * 5,
            "turnovers": stats["turnovers_per_game"] * 5,
            "plus_minus": 0,  # Non disponible
            "minutes_played": 40.0  # Standard NBA
        })
        
        impact_result["nba_stats"] = stats
        impact_result["disclaimer"] = "Prédiction basée sur une adaptation des stats NBA"
        
        return impact_result
        
    except Exception as e:
        return {"error": f"Erreur prédiction impact NBA: {str(e)}"}

# =============================================================================
# OUTIL WEB – Recherche d'informations basketball
# =============================================================================
# Remplace l'outil search_basketball_info par celui-ci (DuckDuckGo = 0 blocage)
@app.post("/tools/search_basketball_info")
async def search_basketball_info(query: str = Body(..., embed=True), max_results: int = Body(5)):
    try:
        import duckduckgo_search
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(f"{query} basketball", max_results=max_results)]
        return {
            "query": query,
            "results": [{"title": r["title"], "url": r["href"]} for r in results],
            "source": "DuckDuckGo"
        }
    except:
        return {"results": [], "source": "DuckDuckGo (indisponible)"}

# =============================================================================
# OUTIL COMPARAISON – Comparaison joueurs LFB/NBA
# =============================================================================
@app.post("/tools/compare_players")
async def compare_players(player1: str = Body(..., embed=True), player2: str = Body(..., embed=True)):
    """
    Compare deux joueurs (peut mélanger LFB et NBA)
    """
    logger.info(f"MCP → compare_players: {player1} vs {player2}")
    try:
        # Déterminer le type de chaque joueur (LFB ou NBA)
        def get_player_type(player_name):
            # Vérifier si le joueur existe dans les données LFB
            lfb_players = df[~df['is_team']]['player_name'].unique()
            if player_name in lfb_players:
                return "LFB"
            else:
                return "NBA"
        
        player1_type = get_player_type(player1)
        player2_type = get_player_type(player2)
        
        # Récupérer les impacts selon le type
        impacts = {}
        
        if player1_type == "LFB":
            # Utiliser l'impact LFB existant
            #impact1 = await get_player_impact("sample_match", player1)
            impact1 = get_player_impact_sync("sample_match", player1)
            impacts[player1] = impact1.get("predicted_impact", 0)
        else:
            # Utiliser l'impact NBA
            impact1 = await get_nba_player_impact(player1)
            impacts[player1] = impact1.get("predicted_impact", 0)
        
        if player2_type == "LFB":
            impact2 = await get_player_impact("sample_match", player2)
            impacts[player2] = impact2.get("predicted_impact", 0)
        else:
            impact2 = await get_nba_player_impact(player2)
            impacts[player2] = impact2.get("predicted_impact", 0)
        
        # Analyse comparative
        comparison = {
            "player1": {"name": player1, "type": player1_type, "impact": impacts[player1]},
            "player2": {"name": player2, "type": player2_type, "impact": impacts[player2]},
            "difference": abs(impacts[player1] - impacts[player2]),
            "stronger_player": player1 if impacts[player1] > impacts[player2] else player2
        }
        
        return comparison
        
    except Exception as e:
        return {"error": f"Erreur comparaison: {str(e)}"}
# =============================================================================
# Autres outils (get_team_form, search_guidelines, etc.) – garde-les
# =============================================================================

@app.post("/tools/get_team_form")
async def get_team_form(team_name: str = Body(..., embed=True), last_matches: int = Body(5)):
    try:
        team_data = df[(df['team_name'] == team_name) & (df['is_team'])]
        recent = team_data.sort_values('date', ascending=False).head(last_matches)
        form = ['W' if p > 70 else 'L' for p in recent['points']]
        return {"team": team_name, "last_matches": form, "average_points": round(recent['points'].mean(), 1)}
    except:
        return {"error": "Équipe non trouvée"}

@app.post("/tools/search_guidelines")
async def search_guidelines_tool(keyword: str = Body(..., embed=True), max_results: int = Body(3)):
    from rag.search import search_guidelines  # ← import manquant !
    try:
        results = search_guidelines(keyword, max_results)  # ← await pas nécessaire ici
        return {
            "guidelines_found": [r["content"] for r in results.get("search_results", [])],
            "source": "RAG local"
        }
    except Exception as e:
        logger.error(f"Erreur RAG: {e}")
        return {"error": str(e)}

@app.post("/tools/get_match_analysis")
async def get_match_analysis(match_id: str = Body(..., embed=True)):
    try:
        match = df[df['match_id'] == match_id]
        teams = match[match['is_team']]['team_name'].unique()
        if len(teams) != 2: return {"error": "Match incomplet"}
        t1, t2 = teams
        return {
            "match_id": match_id,
            "teams": [t1, t2],
            "score": {t1: int(match[match['team_name']==t1]['points'].iloc[0]), t2: int(match[match['team_name']==t2]['points'].iloc[0])},
            "top_players": match[~match['is_team']].nlargest(5, 'points')[['player_name', 'points']].to_dict('records')
        }
    except:
        return {"error": "Match non trouvé"}

@app.post("/tools/get_player_comparison")
async def get_player_comparison(player1: str = Body(..., embed=True), player2: str = Body(..., embed=True)):
    return {"player1": player1, "player2": player2, "status": "Comparaison prête"}

@app.post("/tools/get_training_recommendations")
async def get_training_recommendations(player_name: str = Body(..., embed=True), focus_area: str = Body("all")):
    # ← Ajoute frequency dans les recommandations
    return {
        "player": player_name,
        "recommendations": [
            {"area": "Tir", "exercise": "300 tirs", "frequency": "4x/semaine"},
            {"area": "Défense", "exercise": "Close-outs", "frequency": "3x/semaine"},
            {"area": "Physique", "exercise": "Sprints + plyo", "frequency": "2x/semaine"}
        ]
    }

@app.post("/tools/ask_coach_ai")
async def ask_coach_ai(question: str = Body(..., embed=True)):
    logger.info(f"MCP → ask_coach_ai: {question}")
    from utils.ollama_client import generate_with_ollama
    prompt = f"""
Tu es un coach LFB avec 25 ans d'expérience. Réponds en français, de façon directe, professionnelle et actionable.
Pas de blabla, que du concret.

Question : {question}

Réponse :
"""
    response = generate_with_ollama(prompt)
    return {
        "answer": response,
        "source": "Ollama llama3.1:8b local",
        "model": "llama3.1:8b"
    }

# Dans basketcoach_mcp_server.py
@app.post("/tools/generate_coaching_report")
async def generate_coaching_report(match_id: str = Body(..., embed=True)):
    logger.info(f"MCP → generate_coaching_report pour match {match_id}")
    try:
        from utils.ollama_client import generate_with_ollama
        
        # Récupère les données du match
        analysis = client.get_match_analysis(match_id)
        impact_data = {}
        for player in analysis.get("top_players", []):
            name = player["name"]
            impact = client.get_player_impact(match_id, name)
            if "predicted_impact" in impact:
                impact_data[name] = impact["predicted_impact"]
        
        prompt = f"""
Tu es un coach LFB avec 25 ans d'expérience. Génère un rapport post-match professionnel en français.

Match : {match_id}
Top joueurs : {analysis.get('top_players', [])}
Impacts prédits : {impact_data}

Structure du rapport :
1. Résumé du match
2. Performances individuelles clés
3. Analyse collective
4. Recommandations tactiques et entraînement
5. Conclusion

Sois direct, précis, et actionable.
"""
        report = generate_with_ollama(prompt)
        return {
            "report": report,
            "match_id": match_id,
            "source": "Ollama llama3.1:8b + MCP",
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

def get_player_impact_sync(match_id: str, player_name: str):
    return client.get_player_impact(match_id, player_name)

# =============================================================================
# Lancement
# =============================================================================
if __name__ == "__main__":
    logger.info("BASKETCOACH MCP SERVER – 10 OUTILS – STANDARD OFFICIEL")
    uvicorn.run("basketcoach_mcp_server:app", host="127.0.0.1", port=8000)