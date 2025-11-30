# tests/test_nba_full.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.nba_live import get_matches_by_date, get_boxscore, format_boxscore_for_display
from datetime import datetime, timedelta


def choose_date_and_show_match():
    print("CHOISIS TA DATE NBA (ex: 2025-11-18)")
    date_input = input("Date (YYYY-MM-DD) ou 'hier' ou 'semaine' : ").strip()

    if date_input == "hier":
        date_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    elif date_input == "semaine":
        date_str = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    else:
        date_str = date_input

    matches = get_matches_by_date(date_str)

    if not matches:
        print("Aucun match trouvé")
        return

    print(f"\n{len(matches)} match(s) le {date_str}\n")
    for i, m in enumerate(matches):
        print(f"{i+1}. {m['MATCHUP']} | {m['PTS']}-{m['OPP_PTS']} | Résultat: {m['WL']}")

    choice = int(input("\nNuméro du match à analyser : ")) - 1
    game_id = matches[choice]['GAME_ID']

    print(f"\nBOXSCORE COMPLET – {matches[choice]['MATCHUP']}\n")
    
    # Récupération et affichage du boxscore via nba_live
    df = get_boxscore(game_id)
    formatted_df = format_boxscore_for_display(df)
    
    if not formatted_df.empty:
        print(formatted_df.to_string(index=False))
    else:
        print("Boxscore vide")

    print("\nPrêt pour prédiction ML et rapport Ollama 🔥")


if __name__ == "__main__":
    choose_date_and_show_match()