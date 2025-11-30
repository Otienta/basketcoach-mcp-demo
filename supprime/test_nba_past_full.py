# tests/test_nba_past_full.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.nba_live import get_matches_by_date, get_boxscore, format_boxscore_for_display
from datetime import datetime, timedelta


def show_matches_on_date(date_str):
    """Affiche tous les matchs d'une date donnée."""
    print(f"\nRecherche des matchs NBA le {date_str}...")

    matches = get_matches_by_date(date_str)

    if not matches:
        print(" → Aucun match trouvé")
        return []

    print(f" → {len(matches)} match(s) trouvé(s) !\n")
    
    for match in matches:
        print(f" • {match['MATCHUP']} | Score: {match['PTS']}-{match['OPP_PTS']} | Résultat: {match['WL']}")

    return matches


def show_boxscore(game_id):
    print(f"\nRécupération boxscore du match {game_id}")
    
    df = get_boxscore(game_id)
    formatted_df = format_boxscore_for_display(df)
    
    if not formatted_df.empty:
        print(formatted_df.to_string(index=False))
    else:
        print("Boxscore vide")


if __name__ == "__main__":
    # Dates utiles pour les tests
    show_matches_on_date((datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"))
    show_matches_on_date((datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"))
    show_matches_on_date("2025-11-12")
    show_matches_on_date("2025-10-22")
    
    recent = show_matches_on_date("2025-11-15")
    if recent:
        show_boxscore(recent[0]['GAME_ID'])

    print("\nFIN — Tu peux utiliser n'importe quelle date passée ! 🔥")