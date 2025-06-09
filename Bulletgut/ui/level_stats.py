import pygame as pg
from data.config import SCREEN_WIDTH, SCREEN_HEIGHT

class LevelStats:
    def __init__(self):
        self.font_large = pg.font.Font(None, 48)
        self.font_medium = pg.font.Font(None, 36)
        self.font_small = pg.font.Font(None, 24)

    def render(self, screen, enemies_killed, total_enemies, items_collected, total_items):
        """Affiche l'écran de statistiques de fin de niveau"""
        # Fond semi-transparent
        overlay = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        # Titre
        title_text = self.font_large.render("LEVEL COMPLETE", True, (0, 255, 0))
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        screen.blit(title_text, title_rect)

        # Statistiques des ennemis
        enemies_text = f"ENEMIES: {enemies_killed}/{total_enemies}"
        enemies_color = (0, 255, 0) if enemies_killed == total_enemies else (255, 255, 255)
        enemies_surface = self.font_medium.render(enemies_text, True, enemies_color)
        enemies_rect = enemies_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        screen.blit(enemies_surface, enemies_rect)

        # Statistiques des items
        items_text = f"ITEMS: {items_collected}/{total_items}"
        items_color = (0, 255, 0) if items_collected == total_items else (255, 255, 255)
        items_surface = self.font_medium.render(items_text, True, items_color)
        items_rect = items_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
        screen.blit(items_surface, items_rect)

        # Pourcentages
        enemy_percent = (enemies_killed / total_enemies * 100) if total_enemies > 0 else 100
        item_percent = (items_collected / total_items * 100) if total_items > 0 else 100

        enemy_percent_text = f"({enemy_percent:.0f}%)"
        item_percent_text = f"({item_percent:.0f}%)"

        enemy_percent_surface = self.font_small.render(enemy_percent_text, True, enemies_color)
        item_percent_surface = self.font_small.render(item_percent_text, True, items_color)

        enemy_percent_rect = enemy_percent_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 5))
        item_percent_rect = item_percent_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 35))

        screen.blit(enemy_percent_surface, enemy_percent_rect)
        screen.blit(item_percent_surface, item_percent_rect)

        # Instructions
        instruction_text = "PRESS ENTER TO CONTINUE"
        instruction_surface = self.font_medium.render(instruction_text, True, (255, 255, 0))
        instruction_rect = instruction_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
        screen.blit(instruction_surface, instruction_rect)