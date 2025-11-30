import sys
import os
import time

# Ajoute le chemin du projet au sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importation explicite du serveur (pour déclencher les décorateurs)
import basketcoach_mcp_server

# Force l'initialisation des outils
basketcoach_mcp_server.init_mcp_tools()

# Vérification des outils
tools_count = len(getattr(basketcoach_mcp_server.mcp, 'tools', []))
if tools_count == 0:
    print("ERREUR : Aucun outil MCP enregistré. Vérifie l'initialisation.")
    sys.exit(1)
else:
    print(f"OK : {tools_count} outils MCP enregistrés : {list(basketcoach_mcp_server.mcp.tools.keys())}")
time.sleep(2)
# Import du client
from mcp_direct_client import direct_client as client

print("TEST TOUS LES OUTILS MCP\n")

print("1. Impact joueuse")
print(client.get_player_impact("2051529", "Marine Johannès"))

print("\n2. Classement NBA live")
print(client.get_nba_live_ranking())

print("\n3. Ask Coach IA")
print(client.ask_coach_ai("Comment battre Villeneuve d'Ascq ?"))

print("\n4. Rapport IA")
print(client.generate_coaching_report("2051529"))

print("\nTests terminés.")
