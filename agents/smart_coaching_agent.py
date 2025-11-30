# agents/smart_coaching_agent.py
import asyncio
from mcp_direct_client import direct_client
from utils.ollama_client import generate_with_ollama

class SmartCoachingAgent:
    def __init__(self):
        self.mcp = direct_client

    async def generate_smart_report(self, match_id: str) -> str:
        try:
            # 1. Analyse du match
            match = self.mcp.get_match_analysis(match_id)
            if "error" in match:
                return f"Erreur match : {match['error']}"

            teams = match.get("teams", ["Équipe 1", "Équipe 2"])
            score = match.get("score", {})
            top_players = match.get("top_players", [])

            # 2. Impact réel de chaque top joueuse
            impacts = {}
            for player in top_players:
                name = player.get("player_name") or player.get("name", "Inconnue")
                impact_res = self.mcp.get_player_impact(match_id, name)
                if "predicted_impact" in impact_res:
                    impacts[name] = round(impact_res["predicted_impact"], 1)

            # 3. Prompt ultra-pro pour Ollama
            prompt = f"""
Tu es un coach LFB avec 25 ans d'expérience. Voici les données réelles du match {match_id} :

Match : {teams[0]} vs {teams[1]}
Score final : {score.get(teams[0], '?')} - {score.get(teams[1], '?')}

Top 5 joueuses par impact ML :
{chr(10).join([f"• {name} : {imp} / 50" for name, imp in impacts.items()]) or "Aucune donnée"}

Génère un rapport post-match professionnel en français avec :
1. Résumé du match (1 phrase)
2. Performances individuelles clés (2-3 joueuses)
3. Ce qui a fait la différence
4. 3 recommandations concrètes pour le prochain entraînement
5. Conclusion motivante

Sois direct, précis, et 100 % basé sur ces données.
"""

            report = generate_with_ollama(prompt, model="llama3.1:8b")
            return report

        except Exception as e:
            return f"Erreur génération rapport : {str(e)}"