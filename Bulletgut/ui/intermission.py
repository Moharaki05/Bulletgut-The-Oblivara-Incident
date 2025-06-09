import pygame as pg
from data.config import SCREEN_WIDTH, SCREEN_HEIGHT


class IntermissionScreen:
    def __init__(self):
        self.font_large = pg.font.Font(None, 48)
        self.font_medium = pg.font.Font(None, 36)
        self.font_small = pg.font.Font(None, 24)

        # Charger l'image de fond d'intermission
        try:
            self.background_image = pg.image.load("assets/ui/intermission_bg.png")
            self.background_image = pg.transform.scale(self.background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            # Fallback si l'image n'existe pas
            print("[WARNING] assets/ui/intermission_bg.png not found, using default background")
            self.background_image = None

        # Animation du texte "PRESS ENTER"
        self.blink_timer = 0
        self.blink_interval = 0.8  # Clignote toutes les 0.8 secondes
        self.show_enter_text = True

    def update(self, dt):
        """Met à jour l'animation du texte"""
        self.blink_timer += dt
        if self.blink_timer >= self.blink_interval:
            self.blink_timer = 0
            self.show_enter_text = not self.show_enter_text

    def render(self, screen, enemies_killed, total_enemies, items_collected, total_items):
        """Affiche l'écran d'intermission complet"""
        # Fond d'intermission
        if self.background_image:
            screen.blit(self.background_image, (0, 0))
        else:
            # Fond de couleur par défaut
            screen.fill((20, 20, 40))

            # Ajouter un motif simple si pas d'image
            for i in range(0, SCREEN_WIDTH, 100):
                for j in range(0, SCREEN_HEIGHT, 100):
                    pg.draw.rect(screen, (30, 30, 50), (i, j, 50, 50))

        # Titre principal
        title_text = self.font_large.render("LEVEL COMPLETE", True, (0, 255, 0))
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        screen.blit(title_text, title_rect)

        # Statistiques des ennemis
        enemies_text = f"ENEMIES ELIMINATED: {enemies_killed}/{total_enemies}"
        enemies_color = (0, 255, 0) if enemies_killed == total_enemies else (255, 255, 255)
        enemies_surface = self.font_medium.render(enemies_text, True, enemies_color)
        enemies_rect = enemies_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        screen.blit(enemies_surface, enemies_rect)

        # Pourcentage des ennemis
        enemy_percent = (enemies_killed / total_enemies * 100) if total_enemies > 0 else 100
        enemy_percent_text = f"({enemy_percent:.0f}%)"
        enemy_percent_surface = self.font_small.render(enemy_percent_text, True, enemies_color)
        enemy_percent_rect = enemy_percent_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 25))
        screen.blit(enemy_percent_surface, enemy_percent_rect)

        # Statistiques des items
        items_text = f"ITEMS COLLECTED: {items_collected}/{total_items}"
        items_color = (0, 255, 0) if items_collected == total_items else (255, 255, 255)
        items_surface = self.font_medium.render(items_text, True, items_color)
        items_rect = items_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
        screen.blit(items_surface, items_rect)

        # Pourcentage des items
        item_percent = (items_collected / total_items * 100) if total_items > 0 else 100
        item_percent_text = f"({item_percent:.0f}%)"
        item_percent_surface = self.font_small.render(item_percent_text, True, items_color)
        item_percent_rect = item_percent_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 35))
        screen.blit(item_percent_surface, item_percent_rect)

        # Bonus de performance (optionnel)
        if enemies_killed == total_enemies and items_collected == total_items:
            bonus_text = "PERFECT COMPLETION!"
            bonus_surface = self.font_medium.render(bonus_text, True, (255, 215, 0))  # Couleur or
            bonus_rect = bonus_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
            screen.blit(bonus_surface, bonus_rect)

        # Instructions clignotantes
        if self.show_enter_text:
            instruction_text = "PRESS ENTER TO CONTINUE"
            instruction_surface = self.font_medium.render(instruction_text, True, (255, 255, 0))
            instruction_rect = instruction_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
            screen.blit(instruction_surface, instruction_rect)