# agents/ghost_agent.py
import random
from typing import Tuple, List
from environment.grid import Grid

class GhostAgent:
    def __init__(self, grid: Grid, color: Tuple[int, int, int]):
        self.grid = grid
        self.color = color
        self.actions = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # up, right, down, left
        self.protected = False  # Ghost becomes protected when reaching a flag

    def choose_action(self, position: Tuple[int, int]) -> Tuple[int, int]:
        """
        Choose a random legal action for the ghost, even if protected.
        Returns (dx, dy) representing movement.
        """
        legal_actions = [action for action in self.actions if self.grid.is_valid((position[0] + action[0], position[1] + action[1]))]
        return random.choice(legal_actions) if legal_actions else (0, 0)