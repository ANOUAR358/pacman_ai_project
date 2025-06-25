



# tests/test_agents.py
import unittest
from environment.grid import Grid
from agents.pacman_agent import PacmanAgent
from agents.ghost_agent import GhostAgent
from logic.game import Game

class TestAgents(unittest.TestCase):
    def setUp(self):
        # Create a simple 3x3 grid with P1, F1, G
        map_content = [
            "P1 .",
            ".#F1",
            "G . "
        ]
        with open("test_map.txt", "w") as f:
            f.write("\n".join(map_content))
        self.grid = Grid("test_map.txt")
        self.game = Game("test_map.txt")

    def test_ghost_agent_action(self):
        ghost_agent = GhostAgent(self.grid, (255, 0, 0))
        position = (0, 2)  # Ghost position
        action = ghost_agent.choose_action(position)
        legal_actions = [(0, -1), (1, 0), (0, 1), (-1, 0)]
        legal_actions = [a for a in legal_actions if self.grid.is_valid((position[0] + a[0], position[1] + a[1]))]
        self.assertIn(action, legal_actions)

    def test_pacman_ghost_collision(self):
        self.game.pacman_positions = [(0, 2)]  # Move Pacman to ghost position
        self.game.ghost_positions = [(0, 2)]
        self.game.update()
        self.assertTrue(self.game.game_over)
        self.assertIn("caught by ghost", self.game.game_result)

    def test_pacman_reach_flag(self):
        self.game.pacman_positions = [(2, 1)]  # Move Pacman to flag position
        self.game.ghost_positions = [(0, 2)]
        self.game.update()
        self.assertTrue(self.game.game_over)
        self.assertIn("Victory", self.game.game_result)

if __name__ == '__main__':
    unittest.main()