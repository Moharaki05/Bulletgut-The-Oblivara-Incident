import pygame as pg
import random
from data.config import SCREEN_WIDTH, SCREEN_HEIGHT
from engine.audio_manager import AudioManager


class IntermissionScreen:
    def __init__(self):
        self.font_xlarge = pg.font.Font("assets/fonts/DooM.ttf", 65)
        self.font_large = pg.font.Font("assets/fonts/DooM.ttf", 45)
        self.font_medium = pg.font.Font("assets/fonts/DooM.ttf", 30)
        self.font_small = pg.font.Font("assets/fonts/DooM.ttf", 20)

        # Gestionnaire audio pour l'intermission
        self.audio_manager = AudioManager()
        self.intermission_music_path = "assets/music/intermission.mp3"  # Chemin vers la musique d'intermission

        # Charger l'image de fond d'intermission
        try:
            self.background_image = pg.image.load("assets/ui/intermission_bg.png")
            self.background_image = pg.transform.scale(self.background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except FileNotFoundError:
            # Fallback si l'image n'existe pas
            print("[WARNING] assets/ui/intermission_bg.png not found, using default background")
            self.background_image = None

        # Animation du texte "PRESS ENTER"
        self.blink_timer = 0
        self.blink_interval = 0.8  # Clignote toutes les 0.8 secondes
        self.show_enter_text = True

        # Système de transition rideau ENTRÉE (vers l'intermission)
        self.entry_transition_active = False
        self.entry_transition_in_progress = False
        self.entry_transition_done = False
        self.entry_curtain_col_width = 4
        num_cols = SCREEN_WIDTH // self.entry_curtain_col_width
        self.entry_curtain_columns = [0] * num_cols
        self.entry_curtain_speeds = [random.randint(8, 16) for _ in range(num_cols)]
        self.entry_curtain_surface = None
        self.show_stats = False  # Ne montre les stats qu'après la transition d'entrée

        # Système de transition rideau SORTIE (vers le prochain niveau) - DESCENDANTE
        self.exit_transition_active = False
        self.exit_transition_in_progress = False
        self.exit_transition_done = False
        self.exit_curtain_col_width = 4
        self.exit_curtain_columns = [0] * num_cols  # Commence à 0 (rideau ouvert)
        self.exit_curtain_speeds = [random.randint(8, 16) for _ in range(num_cols)]
        self.exit_curtain_surface = None  # Surface du prochain niveau

        self._intermission_surface = None

        # États de l'intermission
        self.state = "entering"  # "entering", "showing", "exiting", "done"

        # Flag pour s'assurer que la musique ne se lance qu'une fois
        self.music_started = False

    def start_entry_transition(self, game_screen):
        """Démarre la transition rideau vers l'intermission"""
        if not self.entry_transition_active:
            self.entry_transition_active = True
            self.entry_transition_in_progress = True
            self.entry_transition_done = False
            self.show_stats = False
            self.state = "entering"
            self.music_started = False

            # Capturer l'écran actuel pour l'effet rideau
            self.entry_curtain_surface = game_screen.copy()

            # Réinitialiser les colonnes d'entrée
            num_cols = SCREEN_WIDTH // self.entry_curtain_col_width
            self.entry_curtain_columns = [0] * num_cols
            self.entry_curtain_speeds = [random.randint(8, 16) for _ in range(num_cols)]

            print("[INTERMISSION] Starting entry transition")

    def start_exit_transition(self, next_level_screen):
        """Démarre la transition rideau vers le prochain niveau (descendante)"""
        if not self.exit_transition_active and self.state == "showing":
            self.exit_transition_active = True
            self.exit_transition_in_progress = True
            self.exit_transition_done = False
            self.state = "exiting"

            # Arrêter la musique d'intermission
            # self.stop_music()

            # Capturer l'écran du prochain niveau
            self.exit_curtain_surface = next_level_screen.copy()

            # Réinitialiser les colonnes de sortie (commencent ouvertes, vont descendre)
            num_cols = SCREEN_WIDTH // self.exit_curtain_col_width
            self.exit_curtain_columns = [0] * num_cols
            self.exit_curtain_speeds = [random.randint(8, 16) for _ in range(num_cols)]

            print("[INTERMISSION] Starting exit transition and stopping music")

    def start_music(self):
        """Démarre la musique d'intermission"""
        if not self.music_started:
            success = self.audio_manager.load_and_play_music(self.intermission_music_path, loop=-1)
            if success:
                self.music_started = True
                print("[INTERMISSION] Music started successfully")
            else:
                print("[INTERMISSION] Failed to start music")

    def stop_music(self):
        """Arrête la musique d'intermission"""
        if self.music_started:
            self.audio_manager.stop_music()
            self.music_started = False
            print("[INTERMISSION] Music stopped")

    def update(self, dt):
        """Met à jour l'animation du texte et les transitions"""
        # Animation du texte clignotant
        self.blink_timer += dt
        if self.blink_timer >= self.blink_interval:
            self.blink_timer = 0
            self.show_enter_text = not self.show_enter_text

        # Gestion des transitions
        if self.entry_transition_in_progress:
            self.update_entry_curtain_transition()
        elif self.exit_transition_in_progress:
            self.update_exit_curtain_transition()

    def update_entry_curtain_transition(self):
        """Met à jour l'animation du rideau d'entrée"""
        if not self.entry_curtain_surface:
            return

        all_done = True

        for i in range(len(self.entry_curtain_columns)):
            if self.entry_curtain_columns[i] < SCREEN_HEIGHT:
                self.entry_curtain_columns[i] += self.entry_curtain_speeds[i]
                all_done = False

        if all_done and not self.entry_transition_done:
            self.entry_transition_done = True
            self.show_stats = True
            self.entry_transition_in_progress = False
            self.state = "showing"

            # Démarrer la musique d'intermission maintenant que la transition est finie
            self.start_music()

    def update_exit_curtain_transition(self):
        """Met à jour l'animation du rideau de sortie (descendante)"""
        if not self.exit_curtain_surface:
            return

        all_done = True

        for i in range(len(self.exit_curtain_columns)):
            if self.exit_curtain_columns[i] < SCREEN_HEIGHT:
                self.exit_curtain_columns[i] += self.exit_curtain_speeds[i]
                # S'assurer que la colonne ne dépasse pas la hauteur de l'écran
                if self.exit_curtain_columns[i] > SCREEN_HEIGHT:
                    self.exit_curtain_columns[i] = SCREEN_HEIGHT
                all_done = False

        if all_done and not self.exit_transition_done:
            self.exit_transition_done = True
            self.exit_transition_in_progress = False
            self.state = "done"

    def render(self, screen, enemies_killed, total_enemies, items_collected, total_items, map_name=""):
        """Affiche l'écran d'intermission complet avec transitions"""

        # Toujours afficher le prochain niveau en arrière-plan pendant la sortie
        if self.state == "exiting" and self.exit_curtain_surface:
            screen.blit(self.exit_curtain_surface, (0, 0))
        else:
            # Afficher le fond d'intermission normal
            if self.background_image:
                screen.blit(self.background_image, (0, 0))
            else:
                # Fond de couleur par défaut
                screen.fill((20, 20, 40))
                # Ajouter un motif simple si pas d'image
                for i in range(0, SCREEN_WIDTH, 100):
                    for j in range(0, SCREEN_HEIGHT, 100):
                        pg.draw.rect(screen, (30, 30, 50), (i, j, 50, 50))

        # Afficher les statistiques seulement pendant l'état "showing"
        if self.show_stats and self.state == "showing":
            self.render_stats(screen, enemies_killed, total_enemies, items_collected, total_items, map_name)

        # Dessiner les effets rideau appropriés
        if self.entry_transition_in_progress:
            self.draw_entry_curtain_transition(screen)
        elif self.exit_transition_in_progress:
            self.draw_exit_curtain_transition(screen)

    def render_stats(self, screen, enemies_killed, total_enemies, items_collected, total_items, map_name=""):
        """Affiche les statistiques de fin de niveau, avec nom de map"""
        # Nom du niveau
        if map_name:
            name_surface = self.font_xlarge.render(map_name, True, (255, 255, 255))
            name_rect = name_surface.get_rect(center=(SCREEN_WIDTH // 2 + 20, SCREEN_HEIGHT // 4 - 80))
            screen.blit(name_surface, name_rect)

        # Titre principal
        title_text = self.font_large.render("FINISHED", True, (255, 0, 0))
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        screen.blit(title_text, title_rect)

        # Statistiques des ennemis
        enemy_percent = (enemies_killed / total_enemies * 100) if total_enemies > 0 else 100
        enemies_text = f"KILLS : {int(enemy_percent)}%"
        enemies_color = (0, 255, 0) if enemies_killed == total_enemies else (255, 255, 255)
        enemies_surface = self.font_medium.render(enemies_text, True, enemies_color)
        enemies_rect = enemies_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        screen.blit(enemies_surface, enemies_rect)

        # Statistiques des items
        item_percent = (items_collected / total_items * 100) if total_items > 0 else 100
        items_text = f"ITEMS : {int(item_percent)}%"
        items_color = (0, 255, 0) if items_collected == total_items else (255, 255, 255)
        items_surface = self.font_medium.render(items_text, True, items_color)
        items_rect = items_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
        screen.blit(items_surface, items_rect)

        # Instruction clignotante
        if self.show_enter_text and self.state == "showing":
            instruction_text = "PRESS [ENTER] TO CONTINUE"
            instruction_surface = self.font_medium.render(instruction_text, True, (255, 0, 0))
            instruction_rect = instruction_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
            screen.blit(instruction_surface, instruction_rect)

    def draw_entry_curtain_transition(self, screen):
        """Dessine l'effet rideau d'entrée (colonnes qui descendent)"""
        if not self.entry_curtain_surface:
            return

        col_width = self.entry_curtain_col_width

        for x in range(0, SCREEN_WIDTH, col_width):
            col_index = x // col_width
            if col_index >= len(self.entry_curtain_columns):
                continue

            # Calculer la hauteur restante à dessiner
            remaining_height = SCREEN_HEIGHT - self.entry_curtain_columns[col_index]

            if remaining_height > 0:
                # Source: partie de l'écran original qui n'est pas encore "tombée"
                source_rect = pg.Rect(x, self.entry_curtain_columns[col_index], col_width, remaining_height)
                dest_pos = (x, self.entry_curtain_columns[col_index])

                try:
                    column = self.entry_curtain_surface.subsurface(source_rect)
                    screen.blit(column, dest_pos)
                except ValueError:
                    # Gérer les cas où le rectangle sort des limites
                    pass

    def draw_exit_curtain_transition(self, screen):
        """Dessine l'effet rideau de sortie DESCENDANT (colonnes de l'intermission qui tombent)"""
        col_width = self.exit_curtain_col_width

        # Créer une surface temporaire avec le contenu de l'intermission si nécessaire

        self._intermission_surface = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        if self.background_image:
            self._intermission_surface.blit(self.background_image, (0, 0))
        else:
            self._intermission_surface.fill((20, 20, 40))
            for i in range(0, SCREEN_WIDTH, 100):
                for j in range(0, SCREEN_HEIGHT, 100):
                    pg.draw.rect(self._intermission_surface, (30, 30, 50), (i, j, 50, 50))

        # Dessiner les colonnes de l'intermission qui n'ont pas encore "tombé"
        for x in range(0, SCREEN_WIDTH, col_width):
            col_index = x // col_width
            if col_index >= len(self.exit_curtain_columns):
                continue

            # Hauteur restante de l'intermission à afficher (ce qui n'est pas encore tombé)
            curtain_pos = min(self.exit_curtain_columns[col_index], SCREEN_HEIGHT)
            remaining_height = SCREEN_HEIGHT - curtain_pos

            if remaining_height > 0:
                # Dessiner la partie de l'intermission qui reste visible
                source_rect = pg.Rect(x, curtain_pos, col_width, remaining_height)
                dest_pos = (x, curtain_pos)

                # Vérifier que le rectangle source est valide
                if (source_rect.x >= 0 and source_rect.y >= 0 and
                        source_rect.x + source_rect.width <= SCREEN_WIDTH and
                        source_rect.y + source_rect.height <= SCREEN_HEIGHT and
                        source_rect.width > 0 and source_rect.height > 0):
                    try:
                        intermission_column = self._intermission_surface.subsurface(source_rect)
                        screen.blit(intermission_column, dest_pos)
                    except (ValueError, pg.error):
                        # En cas d'erreur, dessiner une colonne de couleur unie
                        pg.draw.rect(screen, (20, 20, 40), (*dest_pos, col_width, remaining_height))

    def is_entry_transition_complete(self):
        """Retourne True si la transition d'entrée est terminée"""
        return self.show_stats and not self.entry_transition_in_progress

    def is_exit_transition_complete(self):
        """Retourne True si la transition de sortie est terminée"""
        return self.exit_transition_done and self.state == "done"

    def can_accept_input(self):
        """Retourne True si l'intermission peut accepter des inputs (ENTER)"""
        return (self.state == "showing" and
                self.show_stats and
                not self.entry_transition_in_progress and
                not self.exit_transition_in_progress)

    def reset(self):
        """Remet l'intermission à zéro pour la prochaine utilisation"""
        # Arrêter la musique si elle joue encore
        # self.stop_music()

        self.entry_transition_active = False
        self.entry_transition_in_progress = False
        self.entry_transition_done = False
        self.exit_transition_active = False
        self.exit_transition_in_progress = False
        self.exit_transition_done = False
        self.show_stats = False
        self.state = "entering"
        self.entry_curtain_surface = None
        self.exit_curtain_surface = None
        self.music_started = False

        # Nettoyer la surface temporaire
        if hasattr(self, '_intermission_surface'):
            del self._intermission_surface

        print("[INTERMISSION] Reset completed")

    # Méthodes de compatibilité avec l'ancien code
    def start_transition(self, game_screen):
        """Alias pour start_entry_transition (compatibilité)"""
        self.start_entry_transition(game_screen)

    def is_transition_complete(self):
        """Alias pour is_entry_transition_complete (compatibilité)"""
        return self.is_entry_transition_complete()