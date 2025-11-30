# tests/test_nba_match.py – VERSION QUI MARCHE EN NOVEMBRE 2025
from nba_api.stats.endpoints import leaguegamefinder, boxscoretraditionalv3
import pandas as pd

print("Recherche d'un match NBA récent de la saison 2025-26...")

# 1. Trouve les matchs récents (depuis le début de saison)
gamefinder = leaguegamefinder.LeagueGameFinder(
    season_nullable="2025-26",
    season_type_nullable="Regular Season"
)
games = gamefinder.get_data_frames()[0]

if games.empty or len(games) == 0:
    print("Aucun match trouvé – la saison n'a peut-être pas encore commencé ou problème réseau")
else:
    # Prend le match le plus récent
    latest_game = games.iloc[0]
    game_id = latest_game['GAME_ID']
    matchup = latest_game['MATCHUP']
    date = latest_game['GAME_DATE']

    print(f"Match trouvé !")
    print(f"Date : {date}")
    print(f"Matchup : {matchup}")
    print(f"Game ID : {game_id}")

    # 2. Boxscore complet
    print(f"\nRécupération du boxscore pour {game_id}...")
    box = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=game_id)
    df = box.get_data_frames()[0]  # player_stats

    # Colonnes qui existent vraiment en 2025-26
    cols_to_show = ['PLAYER_NAME', 'TEAM_ABBREVIATION', 'MIN', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PLUS_MINUS']
    available_cols = [c for c in cols_to_show if c in df.columns]

    if not df.empty:
        print("\n📊 TOP 15 JOUEURS DU MATCH")
        print(df[available_cols].head(15).to_string(index=False))
    else:
        print("Boxscore vide (match pas encore joué ou problème API)")