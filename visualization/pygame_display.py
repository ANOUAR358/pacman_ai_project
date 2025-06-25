# visualization/pygame_display.py
import pygame
from config import settings
from typing import List, Tuple, Dict

class PygameDisplay:
    def __init__(self, grid, flag_colors: Dict[str, Tuple[int, int, int]], scores: Dict[str, dict], high_scores: Dict[str, int]):
        pygame.init()
        self.grid = grid
        self.flag_colors = flag_colors
        self.scores = scores
        self.high_scores = high_scores
        self.cell_size = settings.CELL_SIZE
        self.fps = settings.FPS
        self.padding = self.cell_size
        self.status_bar_width = self.cell_size * 18  # Increased for better visibility
        self.width = self.grid.width * self.cell_size + self.padding * 2 + self.status_bar_width
        self.height = max(self.grid.height * self.cell_size + self.padding * 2, 600)
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Pacman AI - Intelligent Scoring System")
        self.clock = pygame.time.Clock()
        
        # Font setup with larger sizes for clarity
        base_font_size = max(14, min(18, self.cell_size // 2))  # Increased base font size
        self.font = pygame.font.SysFont('Arial', base_font_size)
        self.large_font = pygame.font.SysFont('Arial', base_font_size + 12)  # Larger for headers
        self.title_font = pygame.font.SysFont('Arial', base_font_size + 20)
        
        self.move_count = 0
        self.score_popups = []
        self.score_highlights = {}  # Track score changes for highlight effect
        self.previous_scores = {flag_id: {"traditional": 0, "intelligence": 0.0} for flag_id in scores}
        self.show_help = False
        self.help_surface = None
        self.prepare_help_surface()

    def prepare_help_surface(self):
        """Pre-render the help surface for better performance"""
        help_width = min(800, self.width - 100)
        help_height = min(600, self.height - 100)
        self.help_surface = pygame.Surface((help_width, help_height))
        self.help_surface.fill((0, 0, 50))
        pygame.draw.rect(self.help_surface, (100, 100, 200), (0, 0, help_width, help_height), 3)
        
        title = self.title_font.render("INTELLIGENT SCORING SYSTEM", True, (255, 255, 0))
        self.help_surface.blit(title, (help_width//2 - title.get_width()//2, 30))
        
        y_offset = 80
        explanations = [
            ("TRADITIONAL SCORE", "Points from food (+10) and flags (+100)"),
            ("INTELLIGENCE SCORE (0-10)", "Composite metric evaluating agent performance:"),
            ("- Time Efficiency (30%)", "Points earned quickly score higher"),
            ("- Path Efficiency (40%)", "Optimal path choices (compared to A*)"),
            ("- Decision Quality (20%)", "Percentage of optimal moves made"),
            ("- Safety Score (10%)", "Avoiding ghosts and dangerous areas"),
            ("", "Press H to close this help"),
            ("CONTROLS", "SHIFT+R: Restart game"),
            ("", "ESC: Quit game")
        ]
        
        for label, text in explanations:
            if label:
                label_surf = self.large_font.render(label, True, (255, 255, 0))
                self.help_surface.blit(label_surf, (40, y_offset))
                y_offset += 35
            if text:
                text_surf = self.font.render(text, True, (255, 255, 255))
                self.help_surface.blit(text_surf, (60, y_offset))
                y_offset += 30
            y_offset += 10

    def draw_shape(self, x: int, y: int, shape: str, color: Tuple[int, int, int]):
        """Draw game elements with enhanced visuals"""
        cx = x * self.cell_size + self.padding
        cy = y * self.cell_size + self.padding
        size = self.cell_size
        rect = pygame.Rect(cx, cy, size, size)
        
        if shape == 'rect':  # Walls
            pygame.draw.rect(self.screen, settings.COLOR_WALL, rect)
            pygame.draw.rect(self.screen, (50, 50, 150), rect, 2)
            # Add texture to walls
            for i in range(0, size, 4):
                pygame.draw.line(self.screen, (70, 70, 120), 
                               (cx, cy + i), (cx + size, cy + i), 1)
        
        elif shape == 'circle':  # Food
            center = rect.center
            radius = int(size * 0.15)
            pygame.draw.circle(self.screen, settings.COLOR_FOOD, center, radius)
            # Add shine effect
            pygame.draw.circle(self.screen, (255, 255, 150), 
                             (center[0] - radius//3, center[1] - radius//3), 
                             radius//4)
        
        elif shape == 'pacman':
            center = rect.center
            radius = int(size * 0.4)
            # Body with gradient effect
            for r in range(radius, 0, -2):
                alpha = 255 * r // radius
                color_with_alpha = (color[0], color[1], color[2], alpha)
                s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                pygame.draw.circle(s, color_with_alpha, (r, r), r)
                self.screen.blit(s, (center[0]-r, center[1]-r))
            
            # Mouth
            pygame.draw.polygon(self.screen, (0, 0, 0), [
                center,
                (center[0] + radius, center[1] - radius // 2),
                (center[0] + radius, center[1] + radius // 2)
            ])
            # Eye
            eye_pos = (center[0] - radius//3, center[1] - radius//3)
            pygame.draw.circle(self.screen, (0, 0, 0), eye_pos, radius//6)
        
        elif shape == 'ghost':
            # Body with outline
            body_rect = pygame.Rect(cx + 2, cy + size * 0.2, size - 4, size * 0.6)
            pygame.draw.rect(self.screen, settings.COLOR_GHOST, body_rect, border_radius=8)
            pygame.draw.rect(self.screen, (0, 0, 0), body_rect, border_radius=8, width=2)
            
            # Wavy bottom
            wave_points = []
            for i in range(5):
                wave_x = cx + 2 + (size - 4) * i / 4
                wave_y = cy + size * 0.8 + (10 if i % 2 == 0 else -5)
                wave_points.append((wave_x, wave_y))
            wave_points.append((cx + size - 2, cy + size * 0.8))
            wave_points.append((cx + 2, cy + size * 0.8))
            pygame.draw.polygon(self.screen, settings.COLOR_GHOST, wave_points)
            pygame.draw.polygon(self.screen, (0, 0, 0), wave_points, 2)
            
            # Eyes
            eye_radius = size // 6
            eye_y = int(cy + size * 0.35)
            left_eye_pos = (cx + size // 3, eye_y)
            right_eye_pos = (cx + 2 * size // 3, eye_y)
            
            pygame.draw.circle(self.screen, (255, 255, 255), left_eye_pos, eye_radius)
            pygame.draw.circle(self.screen, (255, 255, 255), right_eye_pos, eye_radius)
            
            # Pupils (look toward nearest pacman)
            pupil_radius = size // 10
            pygame.draw.circle(self.screen, (0, 0, 100), left_eye_pos, pupil_radius)
            pygame.draw.circle(self.screen, (0, 0, 100), right_eye_pos, pupil_radius)
        
        elif shape == 'flag':
            # Pole
            pole_color = (100, 100, 100)
            pygame.draw.line(self.screen, pole_color, 
                           (cx + size // 4, cy + size // 6), 
                           (cx + size // 4, cy + size * 0.9), 5)
            # Flag
            flag_points = [
                (cx + size // 4, cy + size // 6),
                (cx + size // 4 + size // 2, cy + size // 3),
                (cx + size // 4, cy + size // 2)
            ]
            pygame.draw.polygon(self.screen, color, flag_points)
            pygame.draw.polygon(self.screen, (0, 0, 0), flag_points, 2)
            # Flag pattern
            if color == (255, 255, 0):  # Yellow flag
                pygame.draw.line(self.screen, (200, 0, 0), 
                               (cx + size // 4 + 2, cy + size // 6 + 5),
                               (cx + size // 4 + size // 2 - 2, cy + size // 3 - 5), 2)

    def render(self, pacman_positions: List[Tuple[Tuple[int, int], Tuple[int, int, int]]] = None, 
               ghost_positions: List[Tuple[int, int]] = None, scores: Dict[str, dict] = None):
        pacman_positions = pacman_positions or []
        ghost_positions = ghost_positions or []
        self.move_count += 1
        
        # Clear screen with dark background
        self.screen.fill(settings.COLOR_BG)
        
        # Draw game area border with glow effect
        border_rect = pygame.Rect(
            self.padding - 5, 
            self.padding - 5, 
            self.grid.width * self.cell_size + 10, 
            self.grid.height * self.cell_size + 10
        )
        pygame.draw.rect(self.screen, (50, 50, 150), border_rect, 0)
        pygame.draw.rect(self.screen, settings.COLOR_BORDER, border_rect, 5)
        
        # Draw grid elements
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                pos = (x, y)
                if pos in self.grid.walls:
                    self.draw_shape(x, y, 'rect', settings.COLOR_WALL)
                elif pos in self.grid.food_positions:
                    self.draw_shape(x, y, 'circle', settings.COLOR_FOOD)
        
        # Draw flags with team colors
        for fx, fy, flag_id in self.grid.flag_positions:
            color = self.flag_colors.get(flag_id, (255, 255, 255))
            self.draw_shape(fx, fy, 'flag', color)
        
        # Draw ghosts
        for gx, gy in ghost_positions:
            self.draw_shape(gx, gy, 'ghost', settings.COLOR_GHOST)
        
        # Draw pacmans with their team colors
        for (px, py), color in pacman_positions:
            if self.grid.is_valid((px, py)):
                self.draw_shape(px, py, 'pacman', color)
        
        # Detect score changes for highlight effect
        for flag_id, score_data in scores.items():
            if (score_data['traditional'] != self.previous_scores[flag_id]['traditional'] or 
                abs(score_data['intelligence'] - self.previous_scores[flag_id]['intelligence']) > 0.01):
                self.score_highlights[flag_id] = (30, 'change')  # Highlight for 30 frames
            self.previous_scores[flag_id] = score_data.copy()
        
        # Update highlight timers
        for flag_id in list(self.score_highlights):
            frames, highlight_type = self.score_highlights[flag_id]
            if frames > 0:
                self.score_highlights[flag_id] = (frames - 1, highlight_type)
            else:
                del self.score_highlights[flag_id]
        
        # Render sidebar with detailed scores
        self.render_status_bar(scores)
        
        # Render score pop-ups
        self.render_score_popups()
        
        # Show help if toggled
        if self.show_help:
            self.render_help()
        
        pygame.display.flip()
        self.clock.tick(self.fps)

    def render_status_bar(self, scores: Dict[str, dict]):
        sidebar_x = self.grid.width * self.cell_size + self.padding
        sidebar_y = self.padding
        sidebar_height = self.height - self.padding * 2
        
        # Sidebar background with gradient
        for y in range(sidebar_y, sidebar_y + sidebar_height):
            alpha = 255 * (y - sidebar_y) // sidebar_height
            color = (30, 30, 80, alpha)
            s = pygame.Surface((self.status_bar_width, 1), pygame.SRCALPHA)
            s.fill(color)
            self.screen.blit(s, (sidebar_x, y))
        
        # Sidebar border
        pygame.draw.rect(self.screen, (100, 100, 200), 
                        (sidebar_x, sidebar_y, self.status_bar_width, sidebar_height), 2)
        
        # Title with shadow effect
        title_text = self.large_font.render("INTELLIGENT SCORES", True, (0, 0, 0))
        self.screen.blit(title_text, (sidebar_x + 53, sidebar_y + 13))
        title_text = self.large_font.render("INTELLIGENT SCORES", True, (255, 255, 255))
        self.screen.blit(title_text, (sidebar_x + 50, sidebar_y + 10))
        
        y_offset = sidebar_y + 60  # Adjusted for larger fonts
        
        # Player score cards
        for flag_id, score_data in scores.items():
            player_id = f"P{flag_id[1:]}"
            player_color = self.flag_colors.get(flag_id, (255, 255, 255))
            
            # Highlight if score changed recently
            highlight = flag_id in self.score_highlights
            card_color = (40, 40, 90) if not highlight else (60, 60, 110)
            
            # Player score card
            pygame.draw.rect(self.screen, card_color, 
                           (sidebar_x + 10, y_offset, self.status_bar_width - 20, 180))  # Increased height
            pygame.draw.rect(self.screen, (100, 100, 200), 
                           (sidebar_x + 10, y_offset, self.status_bar_width - 20, 180), 2)
            
            # Player header with color indicator
            pygame.draw.rect(self.screen, player_color, (sidebar_x + 20, y_offset + 15, 15, 15))
            header = self.large_font.render(f"{player_id} PERFORMANCE", True, (255, 255, 255))
            self.screen.blit(header, (sidebar_x + 40, y_offset + 10))
            
            # Score breakdown with adjusted spacing
            self.render_score_metric("Points:", f"{score_data['traditional']}", 
                                   sidebar_x + 20, y_offset + 50, highlight)
            self.render_score_metric("Intelligence:", f"{score_data['intelligence']:.1f}/10", 
                                   sidebar_x + 20, y_offset + 80, highlight)
            self.render_score_metric("Time Eff:", f"{score_data['time']:.1f}/10", 
                                   sidebar_x + 20, y_offset + 110, highlight)
            self.render_score_metric("Path Eff:", f"{score_data['path_eff']:.1f}/10", 
                                   sidebar_x + 20, y_offset + 140, highlight)
            self.render_score_metric("Food Collected:", f"{score_data['food_collected']}", 
                                   sidebar_x + 20, y_offset + 170, highlight)
            
            y_offset += 190  # Increased spacing for clarity
        
        # Game stats
        stats_y = y_offset + 20
        pygame.draw.rect(self.screen, (40, 40, 90), 
                        (sidebar_x + 10, stats_y, self.status_bar_width - 20, 80))
        pygame.draw.rect(self.screen, (100, 100, 200), 
                        (sidebar_x + 10, stats_y, self.status_bar_width - 20, 80), 2)
        
        self.render_score_metric("Moves:", f"{self.move_count}", 
                               sidebar_x + 20, stats_y + 15, False)
        self.render_score_metric("Food Left:", f"{len(self.grid.food_positions)}", 
                               sidebar_x + 20, stats_y + 40, False)
        
        # Help prompt
        help_text = "Press H for help"
        self.screen.blit(self.font.render(help_text, True, (150, 150, 255)), 
                        (sidebar_x + 20, stats_y + 65))

    def render_score_metric(self, label: str, value: str, x: int, y: int, highlight: bool):
        """Render a score metric with optional highlight effect"""
        label_color = (200, 200, 255) if highlight else (180, 180, 255)
        value_color = (255, 255, 0) if highlight else (255, 255, 255)
        
        label_surface = self.font.render(label, True, label_color)
        value_surface = self.font.render(value, True, value_color)
        
        self.screen.blit(label_surface, (x, y))
        self.screen.blit(value_surface, (x + 160, y))  # Adjusted for wider sidebar

    def render_help(self):
        """Render the help overlay"""
        help_x = (self.width - self.help_surface.get_width()) // 2
        help_y = (self.height - self.help_surface.get_height()) // 2
        
        # Darken the background
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Draw help surface
        self.screen.blit(self.help_surface, (help_x, help_y))

    def render_score_popups(self):
        """Render animated score pop-ups"""
        for popup in self.score_popups[:]:
            text, x, y, age = popup
            alpha = max(0, 255 - age * 8)
            text.set_alpha(alpha)
            
            # Add slight movement and fade
            self.screen.blit(text, (x, y - age * 2))
            
            # Update popup state
            new_popup = (text, x, y, age + 1)
            popup_index = self.score_popups.index(popup)
            self.score_popups[popup_index] = new_popup
            
            # Remove old popups
            if age > 30:
                self.score_popups.remove(new_popup)

    def render_game_over(self, message: str, victory: bool = False):
        """Enhanced game over screen with detailed scores"""
        # Dark overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        # Title with effect
        title = "VICTORY!" if victory else "GAME OVER"
        title_color = settings.COLOR_VICTORY if victory else settings.COLOR_GAME_OVER
        title_text = self.title_font.render(title, True, title_color)
        title_rect = title_text.get_rect(center=(self.width // 2, self.height // 4))
        
        # Add shadow
        shadow_text = self.title_font.render(title, True, (0, 0, 0))
        self.screen.blit(shadow_text, (title_rect.x + 3, title_rect.y + 3))
        self.screen.blit(title_text, title_rect)
        
        # Score cards
        y_offset = self.height // 3
        for flag_id, score_data in self.scores.items():
            player_id = f"P{flag_id[1:]}"
            player_color = self.flag_colors.get(flag_id, (255, 255, 255))
            
            # Score card background
            card_rect = pygame.Rect(
                self.width // 2 - 200, 
                y_offset, 
                400, 
                120
            )
            pygame.draw.rect(self.screen, (40, 40, 90), card_rect)
            pygame.draw.rect(self.screen, (100, 100, 200), card_rect, 3)
            
            # Player header
            pygame.draw.rect(self.screen, player_color, (card_rect.x + 20, card_rect.y + 20, 15, 15))
            header = self.large_font.render(f"{player_id} FINAL SCORE", True, (255, 255, 255))
            self.screen.blit(header, (card_rect.x + 40, card_rect.y + 15))
            
            # Score details
            self.render_final_score("Points:", f"{score_data['traditional']}", 
                                  card_rect.x + 30, card_rect.y + 50)
            self.render_final_score("Intelligence:", f"{score_data['intelligence']:.1f}/10", 
                                  card_rect.x + 30, card_rect.y + 75)
            
            y_offset += 140
        
        # Instructions
        restart_text = "Press SHIFT+R to restart"
        restart_surface = self.large_font.render(restart_text, True, (200, 200, 200))
        restart_rect = restart_surface.get_rect(center=(self.width // 2, y_offset + 40))
        self.screen.blit(restart_surface, restart_rect)
        
        pygame.display.flip()

    def render_final_score(self, label: str, value: str, x: int, y: int):
        """Render score line in game over screen"""
        label_surface = self.font.render(label, True, (200, 200, 255))
        value_surface = self.font.render(value, True, (255, 255, 255))
        self.screen.blit(label_surface, (x, y))
        self.screen.blit(value_surface, (x + 150, y))

    def add_score_popup(self, text: str, x: int, y: int):
        """Add a score popup with enhanced visuals"""
        # Different styles based on score type
        if "Food" in text:
            popup_color = (255, 255, 0)  # Yellow for food
        elif "Flag" in text:
            popup_color = (0, 255, 0)   # Green for flags
        else:
            popup_color = (255, 255, 255)
        
        popup_text = self.font.render(text, True, popup_color)
        popup_x = x * self.cell_size + self.padding
        popup_y = y * self.cell_size + self.padding
        self.score_popups.append((popup_text, popup_x, popup_y, 0))

    def close(self):
        pygame.quit()