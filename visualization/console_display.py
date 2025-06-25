

# visualization/console_display.py
from typing import List, Tuple, Dict

class ConsoleDisplay:
    def __init__(self, grid, flag_colors: Dict[str, Tuple[int, int, int]]):
        self.grid = grid
        self.flag_colors = flag_colors
        self.symbols = {
            'P': 'P',
            'G': 'G',
            'F': 'F',
            '.': '.',
            '#': '#',
            ' ': ' '
        }

    def render(self, pacman_positions: List[Tuple[Tuple[int, int], Tuple[int, int, int]]], 
               ghost_positions: List[Tuple[int, int]]):
        grid = self.grid.get_grid()
        display = []
        for y in range(self.grid.height):
            row = []
            for x in range(self.grid.width):
                pos = (x, y)
                if pos in [p[0] for p in pacman_positions]:
                    row.append('P')
                elif pos in ghost_positions:
                    row.append('G')
                elif any(pos == (fx, fy) for fx, fy, _ in self.grid.flag_positions):
                    row.append('F')
                elif pos in self.grid.food_positions:
                    row.append('.')
                elif pos in self.grid.walls:
                    row.append('#')
                else:
                    row.append(' ')
            display.append(''.join(row))
        for line in display:
            print(line)

    def close(self):
        pass