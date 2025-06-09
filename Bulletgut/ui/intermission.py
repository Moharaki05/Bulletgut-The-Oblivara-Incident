# import pygame as pg
# from data.config import SCREEN_WIDTH, SCREEN_HEIGHT
#
#
# class IntermissionScreen:
#     def __init__(self):
#         self.font_large = pg.font.Font(None, 48)
#         self.font_medium = pg.font.Font(None, 36)
#         self.font_small = pg.font.Font(None, 24)
#
#         # Charger l'image de fond d'intermission
#         try:
#             self.background_image = pg.image.load("assets/ui/intermission_bg.png")
#             self.background_image = pg.transform.scale(self.background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
#         except:
#             # Fallback si l'image n'existe pas
#             print("[WARNING] assets/ui/intermission_bg.png not found, using default background")
#             self.background_image = None
#
#         # Animation du texte "PRESS ENTER"
#         self.blink_timer = 0
#         self.blink_interval = 0.8  # Clignote toutes les 0.8 secondes
#         self.show_enter_text = True
#
#     def update(self, dt):
#         """Met à jour l'animation du texte"""
#         self.blink_timer += dt
#         if self.blink_timer >= self.blink_interval:
#             self.blink_timer = 0
#             self.show_enter_text = not self.show_enter_text
#
#     def render(self, screen, enemies_killed, total_enemies, items_collected, total_items):
#         """Affiche l'écran d'intermission complet"""
#         # Fond d'intermission
#         if self.background_image:
#             screen.blit(self.background_image, (0, 0))
#         else:
#             # Fond de couleur par défaut
#             screen.fill((20, 20, 40))
#
#             # Ajouter un motif simple si pas d'image
#             for i in range(0, SCREEN_WIDTH, 100):
#                 for j in range(0, SCREEN_HEIGHT, 100):
#                     pg.draw.rect(screen, (30, 30, 50), (i, j, 50, 50))
#
#         # Titre principal
#         title_text = self.font_large.render("LEVEL COMPLETE", True, (0, 255, 0))
#         title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
#         screen.blit(title_text, title_rect)
#
#         # Statistiques des ennemis
#         enemy_percent = (enemies_killed / total_enemies * 100) if total_enemies > 0 else 100
#         enemies_text = f"KILLS : {int(enemy_percent)}%"
#         enemies_color = (0, 255, 0) if enemies_killed == total_enemies else (255, 255, 255)
#         enemies_surface = self.font_medium.render(enemies_text, True, enemies_color)
#         enemies_rect = enemies_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
#         screen.blit(enemies_surface, enemies_rect)
#
#         # Statistiques des items
#         item_percent = (items_collected / total_items * 100) if total_items > 0 else 100
#         items_text = f"ITEMS : {int(item_percent)}%"
#         items_color = (0, 255, 0) if items_collected == total_items else (255, 255, 255)
#         items_surface = self.font_medium.render(items_text, True, items_color)
#         items_rect = items_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
#         screen.blit(items_surface, items_rect)
#
#         # Bonus de performance (optionnel)
#         if enemies_killed == total_enemies and items_collected == total_items:
#             bonus_text = "PERFECT COMPLETION!"
#             bonus_surface = self.font_medium.render(bonus_text, True, (255, 215, 0))  # Couleur or
#             bonus_rect = bonus_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
#             screen.blit(bonus_surface, bonus_rect)
#
#         # Instructions clignotantes
#         if self.show_enter_text:
#             instruction_text = "PRESS ENTER TO CONTINUE"
#             instruction_surface = self.font_medium.render(instruction_text, True, (255, 255, 0))
#             instruction_rect = instruction_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
#             screen.blit(instruction_surface, instruction_rect)

import pygame as pg
import random
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

        # Système de transition rideau (comme dans game.py)
        self.transition_active = False
        self.transition_in_progress = False
        self.transition_done = False
        self.curtain_col_width = 4
        num_cols = SCREEN_WIDTH // self.curtain_col_width
        self.curtain_columns = [0] * num_cols
        self.curtain_speeds = [random.randint(16, 32) for _ in range(num_cols)]
        self.curtain_surface = None
        self.show_stats = False  # Ne montre les stats qu'après la transition

    def start_transition(self, game_screen):
        """Démarre la transition rideau vers l'intermission"""
        if not self.transition_active:
            self.transition_active = True
            self.transition_in_progress = True
            self.transition_done = False
            self.show_stats = False

            # Capturer l'écran actuel pour l'effet rideau
            self.curtain_surface = game_screen.copy()

            # Réinitialiser les colonnes
            num_cols = SCREEN_WIDTH // self.curtain_col_width
            self.curtain_columns = [0] * num_cols
            self.curtain_speeds = [random.randint(16, 32) for _ in range(num_cols)]

    def update(self, dt):
        """Met à jour l'animation du texte et la transition"""
        # Animation du texte clignotant
        self.blink_timer += dt
        if self.blink_timer >= self.blink_interval:
            self.blink_timer = 0
            self.show_enter_text = not self.show_enter_text

        # Gestion de la transition rideau
        if self.transition_in_progress:
            self.update_curtain_transition()

    def update_curtain_transition(self):
        """Met à jour l'animation du rideau"""
        if not self.curtain_surface:
            return

        all_done = True

        for i in range(len(self.curtain_columns)):
            if self.curtain_columns[i] < SCREEN_HEIGHT:
                self.curtain_columns[i] += self.curtain_speeds[i]
                all_done = False

        if all_done and not self.transition_done:
            self.transition_done = True
            self.show_stats = True
            self.transition_in_progress = False

    def render(self, screen, enemies_killed, total_enemies, items_collected, total_items):
        """Affiche l'écran d'intermission complet avec transition"""

        # Toujours dessiner le fond d'intermission
        if self.background_image:
            screen.blit(self.background_image, (0, 0))
        else:
            # Fond de couleur par défaut
            screen.fill((20, 20, 40))
            # Ajouter un motif simple si pas d'image
            for i in range(0, SCREEN_WIDTH, 100):
                for j in range(0, SCREEN_HEIGHT, 100):
                    pg.draw.rect(screen, (30, 30, 50), (i, j, 50, 50))

        # Afficher les statistiques seulement après la transition
        if self.show_stats:
            self.render_stats(screen, enemies_killed, total_enemies, items_collected, total_items)

        # Dessiner l'effet rideau par-dessus si la transition est en cours
        if self.transition_in_progress:
            self.draw_curtain_transition(screen)

    def render_stats(self, screen, enemies_killed, total_enemies, items_collected, total_items):
        """Affiche les statistiques de fin de niveau"""
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

    def draw_curtain_transition(self, screen):
        """Dessine l'effet rideau (colonnes qui descendent)"""
        if not self.curtain_surface:
            return

        col_width = self.curtain_col_width

        for x in range(0, SCREEN_WIDTH, col_width):
            col_index = x // col_width
            if col_index >= len(self.curtain_columns):
                continue

            # Calculer la hauteur restante à dessiner
            remaining_height = SCREEN_HEIGHT - self.curtain_columns[col_index]

            if remaining_height > 0:
                # Source: partie de l'écran original qui n'est pas encore "tombée"
                source_rect = pg.Rect(x, self.curtain_columns[col_index], col_width, remaining_height)
                dest_pos = (x, self.curtain_columns[col_index])

                try:
                    column = self.curtain_surface.subsurface(source_rect)
                    screen.blit(column, dest_pos)
                except ValueError:
                    # Gérer les cas où le rectangle sort des limites
                    pass

    def is_transition_complete(self):
        """Retourne True si la transition est terminée"""
        return self.show_stats and not self.transition_in_progress