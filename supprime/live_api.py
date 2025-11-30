# utils/live_api.py
import os
import requests
from dotenv import load_dotenv
from utils.logger import get_logger

load_dotenv()
logger = get_logger("live_api")

API_KEY = os.getenv("API_SPORTS_KEY")
BASE_URL = "https://v3.basketball.api-sports.io"

headers = {"x-apisports-key": API_KEY} if API_KEY else {}

def get_lfb_standings(season=2025):
    if not API_KEY:
        logger.warning("Pas de clé API → mode offline")
        return {"errors": "Pas de clé API"}
    
    params = {"league": "136", "season": season}
    try:
        r = requests.get(f"{BASE_URL}/standings", headers=headers, params=params, timeout=8)
        if r.status_code == 200:
            data = r.json()
            if data.get("response"):
                logger.info(f"Classement LFB {season} récupéré (LIVE)")
                return data
    except requests.exceptions.RequestException as e:
        logger.warning(f"Connexion API échouée → mode offline : {e}")
    
    # Fallback local/simulé
    logger.info("Retour au classement local/simulé")
    return {
        "response": [[
            {"position": 1, "team": {"name": "LDLC ASVEL Féminin"}, "games": {"win": {"total": 9}, "lose": {"total": 0}}},
            {"position": 2, "team": {"name": "Villeneuve d'Ascq"}, "games": {"win": {"total": 8}, "lose": {"total": 1}}},
            {"position": 3, "team": {"name": "Basket Landes"}, "games": {"win": {"total": 7}, "lose": {"total": 2}}},
        ]]
    }

def get_live_matches():
    """Tous les matchs en direct (monde entier)"""
    logger.info("Récupération matchs live...")
    try:
        r = requests.get(f"{BASE_URL}/games", headers=headers, params={"live": "all"}, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"Erreur live matches: {e}")
        return {"errors": str(e)}

def get_today_games():
    """Matchs du jour en France/Europe"""
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    params = {"date": today, "timezone": "Europe/Paris"}
    try:
        r = requests.get(f"{BASE_URL}/games", headers=headers, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"Erreur today games: {e}")
        return {"errors": str(e)}