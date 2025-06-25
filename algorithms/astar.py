


# algorithms/astar.py
from typing import List, Tuple, Optional
from heapq import heappush, heappop
from environment.grid import Grid

class AStar:
    def __init__(self, grid: Grid):
        self.grid = grid

    def manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """Calculate Manhattan distance between two positions."""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def find_path(self, start: Tuple[int, int], goal: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
        """
        Find shortest path from start to goal using A* algorithm.
        Returns path as list of positions or None if no path exists.
        """
        if not self.grid.is_valid(start) or not self.grid.is_valid(goal):
            return None

        # Priority queue: (f_score, node)
        open_set = [(0, start)]
        # Track visited nodes and their costs
        came_from = {}
        g_score = {start: 0}  # Cost from start to node
        f_score = {start: self.manhattan_distance(start, goal)}  # Estimated total cost

        while open_set:
            _, current = heappop(open_set)

            if current == goal:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return path[::-1]  # Reverse path

            for neighbor in self.grid.get_neighbors(current):
                # Cost to neighbor is 1 (grid movement)
                tentative_g_score = g_score[current] + 1

                if tentative_g_score < g_score.get(neighbor, float('inf')):
                    # Update path and scores
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.manhattan_distance(neighbor, goal)
                    heappush(open_set, (f_score[neighbor], neighbor))

        return None  # No path found