# tests/test_agents_integration.py
import pytest
import asyncio
import sys
import os

# Configuration des imports
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from agents.coaching_agent import CoachingAgent
from agents.scouting_agent import ScoutingAgent
from agents.training_agent import TrainingAgent

class TestAgentsIntegration:
    
    @pytest.mark.asyncio
    async def test_coaching_agent_analysis(self):
        """Test l'analyse stratégique d'un match"""
        agent = CoachingAgent()
        result = await agent.analyze_match_strategy("2051529")
        assert "match_id" in result
        assert "team_analyses" in result
        print("✅ Agent coaching: OK")
    
    @pytest.mark.asyncio 
    async def test_scouting_agent(self):
        """Test le scouting d'un joueur"""
        agent = ScoutingAgent()
        result = await agent.comprehensive_player_scout("Marine Johannès")
        assert "player" in result
        assert "scouting_report" in result
        print("✅ Agent scouting: OK")
    
    @pytest.mark.asyncio
    async def test_training_agent(self):
        """Test la génération de programme d'entraînement"""
        agent = TrainingAgent()
        result = await agent.generate_training_program(
            "Sarah Michel", 
            ["Tir", "Défense"]
        )
        assert "training_program" in result
        assert "player" in result
        print("✅ Agent training: OK")

async def run_all_tests():
    print("🧪 TEST INTÉGRATION AGENTS")
    print("=" * 40)
    
    test_instance = TestAgentsIntegration()
    
    try:
        await test_instance.test_coaching_agent_analysis()
        await test_instance.test_scouting_agent()
        await test_instance.test_training_agent()
        print("🎉 Tous les tests agents ont réussi!")
        return True
    except Exception as e:
        print(f"❌ Échec des tests agents: {e}")
        return False

def main():
    success = asyncio.run(run_all_tests())
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)