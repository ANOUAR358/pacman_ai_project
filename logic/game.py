# logic/game.py
from environment.grid import Grid
from visualization.pygame_display import PygameDisplay
from config import settings
import pygame
from agents.agent_factory import AgentFactory
from typing import List, Tuple, Dict
import time
import math

class Game:
    def __init__(self, map_path: str):
        self.grid = Grid(map_path)
        self.colors = [
            (255, 255, 0),    # Yellow
            (0, 255, 255),    # Cyan
            (255, 0, 255),    # Magenta
            (255, 165, 0)     # Orange
        ]
        self.pacman_positions = self.grid.get_start_positions()
        self.ghost_positions = self.grid.get_ghost_positions()
        self.flag_colors: Dict[str, Tuple[int, int, int]] = {}
        self.pacman_agents = []
        self.ghost_agents = []
        self.scores: Dict[str, dict] = {}  # {flag_id: {"traditional": int, "intelligence": float, "time": float, "path_eff": float}}
        self.high_scores: Dict[str, int] = {}
        self.game_over = False
        self.game_result = ""
        self.protected_pacmans = set()
        self.protected_ghosts = set()  # Track protected ghost indices
        self.move_count = 0
        self.start_time = time.time()
        
        # Initialize agents
        agent_factory = AgentFactory(self.grid, self.colors)
        for i, pos in enumerate(self.pacman_positions):
            flag_id = f'F{i+1}'
            self.flag_colors[flag_id] = self.colors[i % len(self.colors)]
            agent = agent_factory.create_pacman_agent(flag_id)
            self.pacman_agents.append(agent)
            self.scores[flag_id] = {
                "traditional": 0,
                "intelligence": 0.0,
                "time": 0.0,
                "path_eff": 0.0,
                "food_collected": 0,
                "flags_reached": 0
            }
            self.high_scores[flag_id] = 0
        
        for _ in self.ghost_positions:
            agent = agent_factory.create_ghost_agent()
            self.ghost_agents.append(agent)
        
        self.display = PygameDisplay(self.grid, self.flag_colors, self.scores, self.high_scores)
        self.running = True

    def calculate_intelligence_score(self, agent, flag_id: str) -> float:
        """Calculate composite intelligence score considering multiple factors"""
        time_score = max(0, 1 - (time.time() - self.start_time) / 300)  # Time efficiency (0-1)
        path_score = agent.get_path_efficiency()  # Path efficiency (0-1)
        decision_score = agent.get_decision_quality()  # Decision quality (0-1)
        safety_score = agent.get_safety_score()  # Safety (0-1)
        
        # Weighted average
        intelligence_score = (
            0.3 * time_score +
            0.4 * path_score +
            0.2 * decision_score +
            0.1 * safety_score
        ) * 10  # Scale to 0-10
        
        self.scores[flag_id]["intelligence"] = intelligence_score
        self.scores[flag_id]["time"] = time_score * 10
        self.scores[flag_id]["path_eff"] = path_score * 10
        return intelligence_score

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and self.game_over:
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        self.reset()
                elif event.key == pygame.K_h:  # Toggle help
                    self.display.show_help = not self.display.show_help

    def update(self):
        if self.game_over:
            return

        self.move_count += 1
        
        # Update ghost positions
        new_ghost_positions = []
        for i, (pos, agent) in enumerate(zip(self.ghost_positions, self.ghost_agents)):
            action = agent.choose_action(pos)
            new_pos = (pos[0] + action[0], pos[1] + action[1])
            
            if self.grid.is_valid(new_pos):
                new_ghost_positions.append(new_pos)
                # Check if ghost reached any flag
                for fx, fy, flag_id in self.grid.get_flag_positions():
                    if new_pos == (fx, fy) and i not in self.protected_ghosts:
                        agent.protected = True
                        self.protected_ghosts.add(i)
            else:
                new_ghost_positions.append(pos)
        
        self.ghost_positions = new_ghost_positions

        # Update Pacman agents with current ghost positions
        for agent in self.pacman_agents:
            agent.update_ghost_positions(self.ghost_positions)

        # Update Pacman positions and scores
        new_pacman_positions = []
        for i, (pos, agent) in enumerate(zip(self.pacman_positions, self.pacman_agents)):
            flag_id = agent.flag_id
            action = agent.choose_action(pos)
            speed = 2 if agent.protected else 1
            new_pos = (pos[0] + action[0] * speed, pos[1] + action[1] * speed)
            
            if self.grid.is_valid(new_pos) and not agent.protected:
                if self.grid.update_position(pos, new_pos, 'P'):
                    new_pacman_positions.append(new_pos)
                    
                    # Traditional scoring: Food
                    if new_pos in self.grid.food_positions:
                        self.scores[flag_id]["traditional"] += 10
                        self.scores[flag_id]["food_collected"] += 1
                        self.display.add_score_popup("+10 Food", new_pos[0], new_pos[1])
                        print(f"Pacman {flag_id} ate food at {new_pos}! Points: {self.scores[flag_id]['traditional']}")
                    
                    # Traditional scoring: Flag (only if no food remains)
                    if not self.grid.food_positions and self.grid.is_goal(new_pos, flag_id):
                        self.scores[flag_id]["traditional"] += 100
                        self.scores[flag_id]["flags_reached"] += 1
                        agent.protected = True
                        self.protected_pacmans.add(flag_id)
                        self.display.add_score_popup("+100 Flag", new_pos[0], new_pos[1])
                        print(f"Pacman {flag_id} reached flag at {new_pos}! Points: {self.scores[flag_id]['traditional']}")
                    
                    # Intelligence scoring
                    self.calculate_intelligence_score(agent, flag_id)
                else:
                    new_pacman_positions.append(pos)
            else:
                new_pacman_positions.append(pos)
                if agent.protected and self.grid.is_valid(new_pos) and self.grid.update_position(pos, new_pos, 'P'):
                    new_pacman_positions[-1] = new_pos
        
        self.pacman_positions = new_pacman_positions

        # Check collisions: only non-protected ghosts can cause game over
        for i, pacman_pos in enumerate(self.pacman_positions):
            if pacman_pos in self.ghost_positions and not self.pacman_agents[i].protected:
                ghost_index = self.ghost_positions.index(pacman_pos)
                if ghost_index not in self.protected_ghosts:
                    print(f"COLLISION! Pacman {self.pacman_agents[i].flag_id} caught by ghost {ghost_index+1} at {pacman_pos}!")
                    self.end_game(victory=False)
                    return

        # Check victory: all Pacmans must be protected
        if len(self.protected_pacmans) == len(self.pacman_agents):
            print("ALL PACMANS PROTECTED - VICTORY!")
            self.end_game(victory=True)

    def end_game(self, victory: bool):
        self.game_over = True
        
        # Final score calculations
        for flag_id in self.scores:
            self.high_scores[flag_id] = max(
                self.high_scores[flag_id], 
                self.scores[flag_id]["traditional"]
            )
            
            # Final intelligence score adjustment
            time_penalty = max(0, (time.time() - self.start_time) / 60)  # 1 point per minute
            self.scores[flag_id]["intelligence"] = max(0, self.scores[flag_id]["intelligence"] - time_penalty)
        
        self.game_result = "VICTORY!" if victory else "GAME OVER!"

    def render(self):
        pacman_data = []
        for pos, agent in zip(self.pacman_positions, self.pacman_agents):
            if agent.protected:
                protected_color = (agent.color[0]//3, agent.color[1]//3, agent.color[2]//3)
                pacman_data.append((pos, protected_color))
            else:
                pacman_data.append((pos, agent.color))
        
        self.display.render(
            pacman_positions=pacman_data,
            ghost_positions=self.ghost_positions,
            scores=self.scores
        )
        
        if self.game_over:
            self.display.render_game_over(self.game_result, "VICTORY" in self.game_result)

    def reset(self):
        self.grid.reset()
        self.pacman_positions = self.grid.get_start_positions()
        self.ghost_positions = self.grid.get_ghost_positions()
        self.flag_colors.clear()
        self.pacman_agents = []
        self.ghost_agents = []
        self.scores.clear()
        self.game_over = False
        self.game_result = ""
        self.protected_pacmans.clear()
        self.protected_ghosts.clear()
        self.move_count = 0
        self.start_time = time.time()
        
        agent_factory = AgentFactory(self.grid, self.colors)
        for i, pos in enumerate(self.pacman_positions):
            flag_id = f'F{i+1}'
            self.flag_colors[flag_id] = self.colors[i % len(self.colors)]
            agent = agent_factory.create_pacman_agent(flag_id)
            self.pacman_agents.append(agent)
            self.scores[flag_id] = {
                "traditional": 0,
                "intelligence": 0.0,
                "time": 0.0,
                "path_eff": 0.0,
                "food_collected": 0,
                "flags_reached": 0
            }
        
        for _ in self.ghost_positions:
            agent = agent_factory.create_ghost_agent()
            self.ghost_agents.append(agent)
        
        self.display = PygameDisplay(self.grid, self.flag_colors, self.scores, self.high_scores)

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            
            if self.game_over:
                pygame.time.wait(100)
            else:
                self.display.clock.tick(settings.FPS)
        
        self.display.close()