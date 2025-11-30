# test_training_agent.py
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.training_agent import TrainingAgent

async def main():
    print("💪 TEST AGENT TRAINING – Programme pour Marine Sarah Michel\n")
    agent = TrainingAgent()
    
    goals = ["Tir", "Défense", "Physique"]
    program = await agent.generate_training_program("Sarah Michel", goals)
    
    print("="*80)
    print("PROGRAMME PERSONNALISÉ")
    print("="*80)
    print(program.get("training_program", "Erreur"))

if __name__ == "__main__":
    asyncio.run(main())