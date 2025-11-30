# test_coaching_agent.py
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.coaching_agent import CoachingAgent

async def main():
    print("🏀 TEST AGENT COACHING – Analyse réelle du match 2051529\n")
    agent = CoachingAgent()
    
    result = await agent.analyze_match_strategy("2051529")
    
    print("="*80)
    print("RÉSULTAT FINAL AGENT COACHING")
    print("="*80)
    
    print(f"Match: {result.get('match_id')}")
    print(f"Équipes: {list(result.get('team_analyses', {}).keys())}")
    
    for team, data in result.get('team_analyses', {}).items():
        print(f"\n{team}")
        print(f"Forme récente: {data.get('team_form', {}).get('last_matches')}")
        print("Joueuses analysées:")
        for player, impact in data.get('players_analysis', {}).items():
            if isinstance(impact, dict) and "predicted_impact" in impact:
                print(f"  → {player}: {impact['predicted_impact']:.1f} impact")
            else:
                print(f"  → {player}: non trouvé dans ce match")
    
    reco = result.get('strategy_recommendations', {})
    print(f"\nRecommandations:")
    print(f"Offensif: {reco.get('offensive_focus')}")
    print(f"Défensif: {reco.get('defensive_focus')}")

if __name__ == "__main__":
    asyncio.run(main())