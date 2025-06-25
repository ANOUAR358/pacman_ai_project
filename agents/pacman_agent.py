# agents/pacman_agent.py
import random
from typing import Tuple, List, Optional
from environment.grid import Grid
from algorithms.astar import AStar
import math

class PacmanAgent:
    def __init__(self, grid: Grid, flag_id: str, color: Tuple[int, int, int]):
        self.grid = grid
        self.flag_id = flag_id
        self.color = color
        self.protected = False
        self.actions = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # up, right, down, left
        self.astar = AStar(grid)
        self.path: List[Tuple[int, int]] = []
        self.ghost_positions: List[Tuple[int, int]] = []
        self.move_count = 0
        self.total_path_efficiency = 0.0
        self.total_decisions = 0
        self.good_decisions = 0
        self.ghost_encounters = 0
        self.last_ghost_positions = []
        self.ghost_direction_predictions = {}

    # Scoring-related methods needed by Game class
    def get_path_efficiency(self) -> float:
        """Calculate current path efficiency score (0-1)"""
        if self.total_decisions == 0:
            return 0.0
        return self.total_path_efficiency / self.total_decisions

    def get_decision_quality(self) -> float:
        """Calculate decision quality score (0-1)"""
        if self.total_decisions == 0:
            return 0.0
        return self.good_decisions / self.total_decisions

    def get_safety_score(self) -> float:
        """Calculate safety score (0-1)"""
        if self.total_decisions == 0:
            return 1.0
        return 1.0 - (self.ghost_encounters / self.total_decisions)

    def get_intelligence_score(self) -> float:
        """Calculate composite intelligence score (0-10)"""
        if self.total_decisions == 0:
            return 0.0
        
        decision_quality = self.get_decision_quality()
        safety_score = self.get_safety_score()
        path_efficiency = self.get_path_efficiency()
        
        intelligence_score = (
            decision_quality * 0.5 +
            safety_score * 0.3 +
            path_efficiency * 0.2
        ) * 10
        
        return max(0, min(10, intelligence_score))

    def update_ghost_positions(self, ghost_positions: List[Tuple[int, int]]):
        """Update ghost positions and track their movement patterns"""
        if self.last_ghost_positions:
            for i, (new_pos, old_pos) in enumerate(zip(ghost_positions, self.last_ghost_positions)):
                if new_pos != old_pos:
                    dx = new_pos[0] - old_pos[0]
                    dy = new_pos[1] - old_pos[1]
                    self.ghost_direction_predictions[i] = (dx, dy)
        
        self.last_ghost_positions = ghost_positions.copy()
        self.ghost_positions = ghost_positions

    def get_flag_position(self) -> Tuple[int, int]:
        """Get the position of this agent's flag"""
        for x, y, fid in self.grid.get_flag_positions():
            if fid == self.flag_id:
                return (x, y)
        raise ValueError(f"Flag {self.flag_id} not found")

    def manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """Calculate Manhattan distance between two positions"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def find_safest_food(self, position: Tuple[int, int]) -> Tuple[int, int]:
        """Find food that maximizes safety and score, or flag if no food remains"""
        food_positions = self.grid.get_food_positions()
        if not food_positions:
            return self.get_flag_position()  # Target flag when no food left

        scored_food = []
        for food_pos in food_positions:
            # Base score (inverse of distance)
            distance = self.manhattan_distance(position, food_pos)
            base_score = 1.0 / (distance + 1)  # +1 to avoid division by zero
            
            # Safety score
            min_ghost_dist = min(
                self.manhattan_distance(food_pos, ghost_pos) 
                for ghost_pos in self.ghost_positions
            )
            safety_score = min_ghost_dist / (self.grid.width + self.grid.height)
            
            # Ghost movement prediction
            threat_score = 0
            for ghost_idx, ghost_pos in enumerate(self.ghost_positions):
                if ghost_idx in self.ghost_direction_predictions:
                    dx, dy = self.ghost_direction_predictions[ghost_idx]
                    predicted_path = self.predict_ghost_path(ghost_pos, (dx, dy))
                    if food_pos in predicted_path:
                        threat_score += 0.5  # Higher threat if ghost might intercept

            total_score = base_score * 0.6 + safety_score * 0.4 - threat_score
            scored_food.append((total_score, food_pos))
        
        # Return position with highest score
        return max(scored_food, key=lambda x: x[0])[1]

    def predict_ghost_path(self, ghost_pos: Tuple[int, int], direction: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Predict ghost's path based on its current direction"""
        path = []
        x, y = ghost_pos
        dx, dy = direction
        
        for _ in range(3):  # Predict 3 moves ahead
            x += dx
            y += dy
            if not self.grid.is_valid((x, y)):
                # Ghost hit a wall, try to find new direction
                possible_moves = [
                    (ndx, ndy) for ndx, ndy in self.actions 
                    if self.grid.is_valid((x + ndx, y + ndy))
                ]
                if possible_moves:
                    dx, dy = random.choice(possible_moves)
                else:
                    break
            path.append((x, y))
        
        return path

    def is_position_safe(self, pos: Tuple[int, int], lookahead: int = 2) -> bool:
        """Check if position is safe considering ghost movement predictions"""
        # Immediate danger check
        for ghost_pos in self.ghost_positions:
            if self.manhattan_distance(pos, ghost_pos) <= 1:
                return False
        
        # Predictive danger check
        for ghost_idx, ghost_pos in enumerate(self.ghost_positions):
            if ghost_idx in self.ghost_direction_predictions:
                dx, dy = self.ghost_direction_predictions[ghost_idx]
                predicted_path = self.predict_ghost_path(ghost_pos, (dx, dy))
                if pos in predicted_path[:lookahead]:
                    return False
        
        return True

    def get_escape_route(self, position: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """Find safest escape route when ghosts are nearby"""
        safe_moves = []
        danger_moves = []
        
        for action in self.actions:
            new_pos = (position[0] + action[0], position[1] + action[1])
            if self.grid.is_valid(new_pos):
                if self.is_position_safe(new_pos, lookahead=3):
                    safe_moves.append(action)
                else:
                    danger_moves.append(action)
        
        # Prefer safe moves, but if none exist, choose least dangerous
        if safe_moves:
            return random.choice(safe_moves)
        elif danger_moves:
            # Choose move that maximizes distance from nearest ghost
            def distance_score(move):
                new_pos = (position[0] + move[0], position[1] + move[1])
                return min(
                    self.manhattan_distance(new_pos, ghost_pos)
                    for ghost_pos in self.ghost_positions
                )
            return max(danger_moves, key=distance_score)
        
        return None

    def choose_action(self, position: Tuple[int, int]) -> Tuple[int, int]:
        """Choose the next action for Pacman"""
        if self.protected:
            return (0, 0)

        # First priority: avoid immediate danger
        if not self.is_position_safe(position):
            escape_move = self.get_escape_route(position)
            if escape_move:
                self.total_decisions += 1
                self.ghost_encounters += 1
                return escape_move

        # Second priority: follow optimal path to food or flag
        if not self.path or position != self.path[0]:
            goal = self.find_safest_food(position)
            self.path = self.astar.find_path(position, goal) or []
            
            # If path is unsafe, find alternative
            if self.path and any(not self.is_position_safe(pos) for pos in self.path[1:3]):
                self.path = []

        if len(self.path) > 1:
            next_pos = self.path[1]
            if self.is_position_safe(next_pos, lookahead=3):
                action = (next_pos[0] - position[0], next_pos[1] - position[1])
                self.path.pop(0)
                self.total_decisions += 1
                self.good_decisions += 1
                
                # Update path efficiency metric
                optimal_path = self.astar.find_path(position, next_pos) or []
                actual_length = 1
                optimal_length = len(optimal_path) - 1 if optimal_path else 1
                efficiency = optimal_length / actual_length if actual_length > 0 else 1.0
                self.total_path_efficiency += min(efficiency, 1.0)
                
                return action
            else:
                self.path = []

        # Fallback: find safest available move
        legal_actions = []
        for action in self.actions:
            new_pos = (position[0] + action[0], position[1] + action[1])
            if self.grid.is_valid(new_pos):
                safety = 1 if self.is_position_safe(new_pos) else 0.5
                legal_actions.append((safety, action))
        
        if legal_actions:
            # Choose safest move
            legal_actions.sort(reverse=True)
            best_safety = legal_actions[0][0]
            best_actions = [action for safety, action in legal_actions if safety == best_safety]
            action = random.choice(best_actions)
            
            self.total_decisions += 1
            if best_safety == 1:
                self.good_decisions += 1
            else:
                self.ghost_encounters += 1
            
            return action
        
        # No moves available
        self.ghost_encounters += 1
        return (0, 0)