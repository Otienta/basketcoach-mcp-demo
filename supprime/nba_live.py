# utils/nba_live.py – VERSION OPTIMISÉE NBA 2025-26
from nba_api.stats.endpoints import leaguegamefinder, boxscoretraditionalv3
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import get_logger
import pandas as pd

logger = get_logger("nba_live")

def get_matches_by_date(date_str: str):
    """Retourne tous les matchs d'une date (format YYYY-MM-DD)"""
    logger.info(f"Récupération matchs NBA du {date_str}")
    try:
        finder = leaguegamefinder.LeagueGameFinder(
            date_from_nullable=date_str, 
            date_to_nullable=date_str,
            league_id_nullable="00"
        )
        games = finder.get_data_frames()[0]
        
        if games.empty:
            logger.info(f"Aucun match trouvé pour {date_str}")
            return []
        
        # Nettoyage et enrichissement des données
        games = games[['GAME_ID', 'TEAM_ID', 'MATCHUP', 'WL', 'PTS']]
        
        # Ajouter les points adverses (OPP_PTS)
        matches = []
        for _, row in games.iterrows():
            opponent_row = games[
                (games["GAME_ID"] == row["GAME_ID"]) & 
                (games["TEAM_ID"] != row["TEAM_ID"])
            ]
            
            opp_pts = int(opponent_row["PTS"].values[0]) if not opponent_row.empty else None
            
            matches.append({
                "GAME_ID": row["GAME_ID"],
                "MATCHUP": row["MATCHUP"],
                "PTS": int(row["PTS"]),
                "OPP_PTS": opp_pts,
                "WL": row["WL"]
            })
        
        logger.info(f"{len(matches)} match(s) trouvé(s) pour {date_str}")
        return matches
        
    except Exception as e:
        logger.error(f"Erreur NBA date {date_str}: {e}")
        return []

def get_boxscore(game_id: str):
    """Retourne le boxscore complet d'un match avec formatage optimisé"""
    logger.info(f"Récupération boxscore NBA {game_id}")
    try:
        box = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=game_id)
        df = box.get_data_frames()[0]
        
        # Filtrer les joueurs qui ont effectivement joué
        if 'minutes' in df.columns:
            df = df[df['minutes'].notna() & (df['minutes'] != '0:00') & (df['minutes'] != '')]
        
        return df
        
    except Exception as e:
        logger.error(f"Erreur boxscore {game_id}: {e}")
        return pd.DataFrame()

def format_boxscore_for_display(boxscore_df):
    """Formate le boxscore pour l'affichage avec les colonnes françaises"""
    if boxscore_df.empty:
        return pd.DataFrame()
    
    # Mapping des colonnes V3 vers l'affichage français
    display_cols = []
    column_mapping = {}
    
    # Colonnes de base (joueur et équipe)
    if 'nameI' in boxscore_df.columns:
        display_cols.append('nameI')
        column_mapping['nameI'] = 'JOUEUR'
    elif 'playerName' in boxscore_df.columns:
        display_cols.append('playerName')
        column_mapping['playerName'] = 'JOUEUR'
    
    if 'teamTricode' in boxscore_df.columns:
        display_cols.append('teamTricode')
        column_mapping['teamTricode'] = 'EQ'
    
    # Statistiques principales
    stat_cols = {
        'minutes': 'MIN',
        'points': 'PTS', 
        'reboundsTotal': 'REB',
        'assists': 'AST',
        'steals': 'STL',
        'blocks': 'BLK',
        'turnovers': 'TOV',
        'plusMinusPoints': '+/-'
    }
    
    for api_col, display_name in stat_cols.items():
        if api_col in boxscore_df.columns:
            display_cols.append(api_col)
            column_mapping[api_col] = display_name
    
    if display_cols:
        display_df = boxscore_df[display_cols].rename(columns=column_mapping)
        return display_df
    else:
        return pd.DataFrame()

def get_recent_matches(days_back: int = 7):
    """Récupère les matchs des derniers jours"""
    recent_matches = []
    for i in range(1, days_back + 1):
        date_str = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        matches = get_matches_by_date(date_str)
        if matches:
            recent_matches.extend(matches)
    
    return recent_matches
