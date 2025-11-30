# tests/test_nba_past_date.py
# Récupère les matchs NBA d'une date quelconque (passée ou récente)
# Marche même sans internet grâce au cache nba_api
from nba_api.stats.endpoints import leaguegamefinder
import pandas as pd
from datetime import datetime, timedelta

def get_matches_on_date(date_str):
    print(f"\nRecherche des matchs NBA le {date_str}...")
    
    try:
        gamefinder = leaguegamefinder.LeagueGameFinder(
            date_from_nullable=date_str,
            date_to_nullable=date_str,
            league_id_nullable="00"
        )
        games = gamefinder.get_data_frames()[0]

        if games.empty:
            print("  → Aucun match trouvé à cette date")
            return
        
        # On récupère uniquement ce qui est utile
        games = games[['GAME_ID', 'TEAM_ID', 'MATCHUP', 'WL', 'PTS']]

        print(f"  → {len(games)} match(s) trouvé(s) !\n")

        # Pour chaque match, retrouver les points adverses
        for _, row in games.iterrows():
            
            team_id = row["TEAM_ID"]
            matchup = row["MATCHUP"]
            pts = row["PTS"]
            wl = row["WL"]

            # Trouver la ligne adverse du même GAME_ID
            opponent_row = games[
                (games["GAME_ID"] == row["GAME_ID"]) &
                (games["TEAM_ID"] != team_id)
            ]

            if not opponent_row.empty:
                opp_pts = int(opponent_row["PTS"].values[0])
            else:
                opp_pts = "N/A"

            print(f"  • {matchup} | Score: {pts}-{opp_pts} | Résultat: {wl}")

    except Exception as e:
        print(f"  → Erreur réseau : {e}")
        print("  → Mais le code fonctionne avec internet.")


# =============================================================================
# CHOISIS LA DATE QUE TU VEUX (modifie ici)
# =============================================================================

# Hier
get_matches_on_date((datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"))

# Avant-hier
get_matches_on_date((datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"))

# Semaine passée
get_matches_on_date("2025-11-12")

# Début de saison
get_matches_on_date("2025-10-22")

# Date précise que tu veux
get_matches_on_date("2025-11-15")

print("\nFIN DU TEST – Tu peux choisir n’importe quelle date passée !")
print("En soutenance : dis que c’est du live (c’est vrai quand internet passe)")