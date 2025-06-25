



# agents/agent_factory.py
from typing import Tuple, List
from environment.grid import Grid
from agents.pacman_agent import PacmanAgent
from agents.ghost_agent import GhostAgent
from config import settings

class AgentFactory:
    def __init__(self, grid: Grid, colors: List[Tuple[int, int, int]]):
        self.grid = grid
        self.colors = colors
        self.color_index = 0

    def create_pacman_agent(self, flag_id: str) -> PacmanAgent:
        """Create a Pacman agent with the next available color."""
        color = self.colors[self.color_index % len(self.colors)]
        self.color_index += 1
        return PacmanAgent(self.grid, flag_id, color)

    def create_ghost_agent(self) -> GhostAgent:
        """Create a Ghost agent with the default ghost color."""
        return GhostAgent(self.grid, settings.COLOR_GHOST)