import os
from typing import List, Tuple

class Grid:
    def __init__(self, map_path):
        self.map_path = map_path
        self.grid = []
        self.pacman_start_positions = []
        self.ghost_positions = []
        self.food_positions = []
        self.flag_positions = []
        self.walls = []
        self._load_map()
        self.height = len(self.grid)
        self.width = len(self.grid[0]) if self.grid else 0
        self._validate_counts()

    def _load_map(self):
        print(f"Loading map from {self.map_path}")
        with open(self.map_path, 'r') as f:
            lines = [line.rstrip('\n') for line in f if line.rstrip('\n')]
        max_width = max(len(line) for line in lines)
        for y, line in enumerate(lines):
            row = []
            x = 0
            print(f"Parsing line {y}: {line}")
            while x < len(line):
                if x + 1 < len(line) and line[x:x+2] in ['P1', 'P2', 'F1', 'F2']:
                    token = line[x:x+2]
                    print(f"Found token '{token}' at ({x}, {y})")
                    if token.startswith('P'):
                        self.pacman_start_positions.append((x, y))
                    elif token.startswith('F'):
                        self.flag_positions.append((x, y, token))
                    row.append(' ')
                    x += 2
                else:
                    char = line[x]
                    print(f"Found char '{char}' at ({x}, {y})")
                    if char == 'G':
                        self.ghost_positions.append((x, y))
                        row.append(' ')
                    elif char == '.':
                        self.food_positions.append((x, y))
                        row.append(' ')
                    elif char == '#':
                        self.walls.append((x, y))
                        row.append('#')  # Keep the wall character in the grid
                    else:
                        row.append(' ')
                    x += 1
            row.extend([' '] * (max_width - len(row)))
            self.grid.append(row)
        for row in self.grid:
            row.extend([' '] * (max_width - len(row)))
        print(f"Pacman positions: {self.pacman_start_positions}")
        print(f"Flag positions: {self.flag_positions}")
        print(f"Ghost positions: {self.ghost_positions}")
        print(f"Food positions: {self.food_positions}")
        print(f"Wall positions: {self.walls}")

    def _validate_counts(self):
        pacman_count = len(self.pacman_start_positions)
        flag_count = len(self.flag_positions)
        ghost_count = len(self.ghost_positions)
        if not (pacman_count == flag_count == ghost_count):
            raise ValueError(
                f"Mismatch in counts: {pacman_count} Pacmans, {flag_count} flags, {ghost_count} ghosts"
            )

    def is_wall(self, pos: Tuple[int, int]) -> bool:
        """Check if position is a wall using the walls list for accuracy"""
        return pos in self.walls

    def is_valid(self, pos: Tuple[int, int]) -> bool:
        """Check if position is valid (within bounds and not a wall)"""
        x, y = pos
        # First check bounds
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        # Then check if it's a wall
        return not self.is_wall(pos)

    def get_neighbors(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        x, y = pos
        directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]
        neighbors = []
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if self.is_valid((nx, ny)):
                neighbors.append((nx, ny))
        return neighbors

    def update_position(self, old_pos: Tuple[int, int], new_pos: Tuple[int, int], symbol: str):
        """Update position only if the new position is valid"""
        if self.is_valid(new_pos):
            ox, oy = old_pos
            nx, ny = new_pos
            # Only clear old position if it's within bounds
            if 0 <= oy < self.height and 0 <= ox < self.width:
                self.grid[oy][ox] = ' '
            # Set new position
            self.grid[ny][nx] = symbol
            # Remove food if pacman eats it
            if new_pos in self.food_positions:
                self.food_positions.remove(new_pos)
            return True
        return False

    def is_goal(self, pos: Tuple[int, int], flag_id: str) -> bool:
        for x, y, fid in self.flag_positions:
            if pos == (x, y) and fid == flag_id:
                return True
        return False

    def get_grid(self) -> List[List[str]]:
        return self.grid

    def get_start_positions(self) -> List[Tuple[int, int]]:
        return self.pacman_start_positions

    def get_flag_positions(self) -> List[Tuple[int, int, str]]:
        return self.flag_positions

    def get_food_positions(self) -> List[Tuple[int, int]]:
        return self.food_positions

    def get_ghost_positions(self) -> List[Tuple[int, int]]:
        return self.ghost_positions

    def reset(self):
        self.grid = []
        self.pacman_start_positions = []
        self.ghost_positions = []
        self.food_positions = []
        self.flag_positions = []
        self.walls = []
        self._load_map()
        self._validate_counts()

    def print_grid(self):
        for row in self.grid:
            print(''.join(row))

    def get_legal_actions(self, position: Tuple[int, int]) -> List[str]:
        actions = []
        x, y = position
        directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # up, right, down, left
        direction_names = ['UP', 'RIGHT', 'DOWN', 'LEFT']
        
        for i, (dx, dy) in enumerate(directions):
            if self.is_valid((x + dx, y + dy)):
                actions.append(direction_names[i])
        return actions