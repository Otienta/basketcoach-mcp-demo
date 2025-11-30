# basketcoach-mcp/agents/__init__.py
"""
Agents spécialisés pour BasketCoach MCP
"""

from .coaching_agent import CoachingAgent
from .scouting_agent import ScoutingAgent
from .training_agent import TrainingAgent

__all__ = ["CoachingAgent", "ScoutingAgent", "TrainingAgent"]