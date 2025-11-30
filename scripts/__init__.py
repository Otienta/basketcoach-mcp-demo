# basketcoach-mcp/scripts/__init__.py
"""
Scripts pour BasketCoach MCP
"""

from .run_mcp_server import main as run_mcp_server
from .run_training import main as run_training
from .setup_environment import main as setup_environment

__all__ = ["run_mcp_server", "run_training", "setup_environment"]