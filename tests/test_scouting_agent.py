# test_scouting_agent.py
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.scouting_agent import ScoutingAgent

async def main():
    print("🔍 TEST AGENT SCOUTING – Marine Johannès\n")
    agent = ScoutingAgent()
    
    result = await agent.comprehensive_player_scout("Marine Johannès")
    
    print("="*80)
    print("RAPPORT SCOUTING MARINE JOHANNÈS")
    print("="*80)
    
    score = result.get('scouting_score', {})
    print(f"Score global: {score.get('overall_score', 'N/A')}")
    print(f"Grade: {score.get('grade', 'N/A')}")
    print(f"Recommandation: {result.get('scouting_report', {}).get('recommendation', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(main())