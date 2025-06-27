import pygame as pg
import math
import random
from data.config import SCREEN_WIDTH, SCREEN_HEIGHT


class LoadingScreen:
    def __init__(self):
        self.font_large = pg.font.Font("assets/fonts/DooM.ttf", 36)
        self.font_medium = pg.font.Font("assets/fonts/DooM.ttf", 24)
        self.font_small = pg.font.Font("assets/fonts/Born2bSportyFS.otf", 18)

        # Couleurs
        self.bg_color = (16, 16, 24)  # Bleu très foncé
        self.text_color = (255, 255, 255)
        self.accent_color = (255, 64, 64)  # Rouge
        self.bar_bg_color = (64, 64, 80)
        self.bar_fill_color = (255, 128, 128)

        # Charger le logo
        self.logo = None
        self.logo_scale = 1.0
        self.fallback_title = False

        try:
            # Essayer de charger le logo depuis le même chemin que le menu principal
            self.logo = pg.image.load("assets/ui/logo.png").convert_alpha()
            # Redimensionner le logo pour l'écran de chargement (un peu plus petit que dans le menu)
            logo_width = min(450, SCREEN_WIDTH - 100)  # Plus petit que dans le menu
            logo_height = int(self.logo.get_height() * (logo_width / self.logo.get_width()))
            self.logo = pg.transform.scale(self.logo, (logo_width, logo_height))

            # Position du logo (centré horizontalement)
            self.logo_x = SCREEN_WIDTH // 2 - self.logo.get_width() // 2
            self.logo_y = SCREEN_HEIGHT // 3 - self.logo.get_height() // 2

            print("[LOADING_SCREEN] Logo loaded successfully")
        except FileNotFoundError:
            # Fallback vers le texte si le logo n'existe pas
            self.fallback_title = True
            print("[LOADING_SCREEN] Logo not found, using text fallback")

        # Animation
        self.progress = 0.0
        self.target_progress = 0.0
        self.animation_time = 0.0
        self.dots_animation = 0.0
        self.pulse_animation = 0.0

        # États de chargement
        self.loading_steps = [
            "Initializing game engine...",
            "Loading textures...",
            "Building level geometry...",
            "Spawning entities...",
            "Loading audio...",
            "Finalizing..."
        ]
        self.current_step = 0
        self.step_duration = 0.3  # Durée de chaque étape en secondes
        self.step_timer = 0.0

        # Particules d'arrière-plan
        self.particles = []
        for _ in range(20):
            self.particles.append({
                'x': pg.math.Vector2(
                    random.randint(0, SCREEN_WIDTH),
                    random.randint(0, SCREEN_HEIGHT)
                ),
                'velocity': pg.math.Vector2(
                    random.uniform(-20, 20),
                    random.uniform(-20, 20)
                ),
                'size': random.uniform(1, 3),
                'alpha': random.randint(30, 80)
            })

        # Transition rideau (inspirée de game.py)
        self.curtain_transition = False
        self.curtain_surface = None
        self.curtain_col_width = 4
        num_cols = SCREEN_WIDTH // self.curtain_col_width
        self.curtain_columns = [0] * num_cols
        self.curtain_speeds = [random.randint(12, 24) for _ in range(num_cols)]
        self.curtain_complete = False

        # Délai avant le début de la transition rideau
        self.curtain_delay = 0.5  # 0.5 secondes après la fin du chargement
        self.curtain_delay_timer = 0.0


    def start_loading(self):
        """Démarre le processus de chargement"""
        self.progress = 0.0
        self.target_progress = 0.0
        self.current_step = 0
        self.step_timer = 0.0
        self.animation_time = 0.0

        # Reset de la transition rideau
        self.curtain_transition = False
        self.curtain_surface = None
        self.curtain_complete = False
        self.curtain_delay_timer = 0.0
        num_cols = SCREEN_WIDTH // self.curtain_col_width
        self.curtain_columns = [0] * num_cols
        self.curtain_speeds = [random.randint(12, 24) for _ in range(num_cols)]

    def update(self, dt):
        """Met à jour l'animation de chargement"""
        self.animation_time += dt
        self.dots_animation += dt * 3
        self.pulse_animation += dt * 2

        # Mettre à jour les particules
        for particle in self.particles:
            particle['x'] += particle['velocity'] * dt

            # Wrap around screen
            if particle['x'].x < 0:
                particle['x'].x = SCREEN_WIDTH
            elif particle['x'].x > SCREEN_WIDTH:
                particle['x'].x = 0
            if particle['x'].y < 0:
                particle['x'].y = SCREEN_HEIGHT
            elif particle['x'].y > SCREEN_HEIGHT:
                particle['x'].y = 0

        # Progression automatique des étapes
        if not self.is_complete:
            self.step_timer += dt
            if self.step_timer >= self.step_duration and self.current_step < len(self.loading_steps):
                self.step_timer = 0.0
                self.current_step += 1
                self.target_progress = self.current_step / len(self.loading_steps)

            # Animation fluide de la barre de progression
            if self.progress < self.target_progress:
                self.progress = min(self.target_progress, self.progress + dt * 2)


        # Gérer la transition rideau après le chargement
        if self.is_complete and not self.curtain_transition:
            self.curtain_delay_timer += dt
            if self.curtain_delay_timer >= self.curtain_delay:
                self.start_curtain_transition()

        # Mettre à jour la transition rideau
        if self.curtain_transition and not self.curtain_complete:
            self.update_curtain_transition()

    def start_curtain_transition(self):
        """Démarre la transition rideau"""
        if not self.curtain_transition:
            print("[LOADING_SCREEN] Starting curtain transition")
            self.curtain_transition = True


    def update_curtain_transition(self):
        """Met à jour la transition rideau"""
        all_done = True
        for i in range(len(self.curtain_columns)):
            if self.curtain_columns[i] < SCREEN_HEIGHT:
                self.curtain_columns[i] += self.curtain_speeds[i]
                all_done = False

        if all_done:
            self.curtain_complete = True
            print("[LOADING_SCREEN] Curtain transition complete")

    def is_finished(self):
        """Retourne True si le chargement ET la transition rideau sont terminés"""
        return self.curtain_complete

    def render_loading_content(self, surface):
        """Rend le contenu de l'écran de chargement sur la surface donnée"""
        surface.fill(self.bg_color)

        # Particules d'arrière-plan
        for particle in self.particles:
            pg.draw.circle(surface, self.accent_color[:3],
                           (int(particle['x'].x), int(particle['x'].y)),
                           int(particle['size']))

        # Afficher le logo avec effet de pulse
        self.render_logo_with_pulse(surface)

        # Barre de progression - ajustée pour être plus bas si on utilise le logo
        bar_y_offset = 150 if (self.logo and not self.fallback_title) else 100
        bar_width = 400
        bar_height = 20
        bar_x = SCREEN_WIDTH // 2 - bar_width // 2
        bar_y = SCREEN_HEIGHT // 2 + bar_y_offset

        # Fond de la barre
        pg.draw.rect(surface, self.bar_bg_color,
                     (bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4))
        pg.draw.rect(surface, (32, 32, 40),
                     (bar_x, bar_y, bar_width, bar_height))

        # Remplissage de la barre avec effet de brillance
        if self.progress > 0:
            fill_width = int(bar_width * self.progress)
            pg.draw.rect(surface, self.bar_fill_color,
                         (bar_x, bar_y, fill_width, bar_height))

            # Effet de brillance qui se déplace
            shine_pos = (self.animation_time * 100) % (bar_width + 50) - 25
            if 0 <= shine_pos <= fill_width:
                pg.draw.rect(surface, (255, 255, 255),
                             (bar_x + shine_pos - 15, bar_y, 30, bar_height))

        # Pourcentage
        percentage = int(self.progress * 100)
        percent_text = self.font_medium.render(f"{percentage}%", True, self.text_color)
        percent_x = SCREEN_WIDTH // 2 - percent_text.get_width() // 2
        percent_y = bar_y + bar_height + 20
        surface.blit(percent_text, (percent_x, percent_y))

        # Texte de l'étape actuelle ou message de completion
        if self.is_complete:
            # Message de completion
            complete_text = self.font_small.render("Good luck, Devil Dog!", True, self.accent_color)
            complete_x = SCREEN_WIDTH // 2 - complete_text.get_width() // 2
            complete_y = percent_y + 60
            surface.blit(complete_text, (complete_x, complete_y))
        elif self.current_step < len(self.loading_steps):
            step_text = self.loading_steps[self.current_step]
            dots_count = int(self.dots_animation) % 4
            step_text += "." * dots_count

            step_surface = self.font_small.render(step_text, True, self.text_color)
            step_x = SCREEN_WIDTH // 2 - step_surface.get_width() // 2
            step_y = percent_y + 60
            surface.blit(step_surface, (step_x, step_y))

        # Instruction - ajustée pour être au bon endroit
        if not self.is_complete:
            instruction_text = self.font_small.render("Preparing your descent into hell...",
                                                      True, (200, 200, 200))
            instruction_x = SCREEN_WIDTH // 2 - instruction_text.get_width() // 2
            instruction_y = SCREEN_HEIGHT - 60
            surface.blit(instruction_text, (instruction_x, instruction_y))

    def render_logo_with_pulse(self, surface):
        """Affiche le logo avec effet de pulse"""
        if self.logo and not self.fallback_title:
            # Effet de pulse sur le logo
            pulse_scale = 1.0 + 0.03 * math.sin(self.pulse_animation)  # Pulse plus subtil pour le logo

            # Redimensionner temporairement le logo pour l'effet de pulse
            current_width = int(self.logo.get_width() * pulse_scale)
            current_height = int(self.logo.get_height() * pulse_scale)
            pulsed_logo = pg.transform.scale(self.logo, (current_width, current_height))

            # Recentrer le logo pulsé
            logo_x = SCREEN_WIDTH // 2 - current_width // 2
            logo_y = SCREEN_HEIGHT // 3 - current_height // 2

            surface.blit(pulsed_logo, (logo_x, logo_y))
        else:
            # Fallback vers le texte avec pulse
            pulse_scale = 1.0 + 0.05 * math.sin(self.pulse_animation)
            title_font = pg.font.Font("assets/fonts/DooM.ttf", int(48 * pulse_scale))
            title_text = title_font.render("BULLETGUT", True, self.accent_color)
            subtitle_text = self.font_medium.render("THE OBLIVARA INCIDENT", True, self.text_color)

            title_x = SCREEN_WIDTH // 2 - title_text.get_width() // 2
            title_y = SCREEN_HEIGHT // 3 - title_text.get_height() // 2

            subtitle_x = SCREEN_WIDTH // 2 - subtitle_text.get_width() // 2
            subtitle_y = title_y + title_text.get_height() + 10

            surface.blit(title_text, (title_x, title_y))
            surface.blit(subtitle_text, (subtitle_x, subtitle_y))

    def draw_curtain_transition(self, screen):
        """Dessine la transition rideau - masque progressivement l'écran de chargement"""
        if not self.curtain_transition:
            return

        # ⭐ NOUVEAU : Créer la surface de l'écran de chargement à la volée
        if not self.curtain_surface:
            self.curtain_surface = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.render_loading_content(self.curtain_surface)

        # Dessiner les colonnes de l'écran de chargement qui restent visibles
        col_width = self.curtain_col_width
        for x in range(0, SCREEN_WIDTH, col_width):
            col_index = x // col_width
            if col_index < len(self.curtain_columns):
                remaining_height = SCREEN_HEIGHT - self.curtain_columns[col_index]
                if remaining_height > 0:
                    # Créer un rectangle source pour cette colonne
                    source_rect = pg.Rect(x, self.curtain_columns[col_index], col_width, remaining_height)
                    dest_pos = (x, self.curtain_columns[col_index])

                    # Vérifier que le rectangle source est valide
                    if (source_rect.x >= 0 and source_rect.y >= 0 and
                            source_rect.right <= self.curtain_surface.get_width() and
                            source_rect.bottom <= self.curtain_surface.get_height()):
                        try:
                            column = self.curtain_surface.subsurface(source_rect)
                            screen.blit(column, dest_pos)
                        except ValueError:
                            # Fallback: dessiner la colonne directement depuis la surface
                            screen.blit(self.curtain_surface, dest_pos, source_rect)

    def render(self, screen, game_screen=None):
        """Affiche l'écran de chargement avec transition rideau optionnelle

        Args:
            screen: Surface principale où dessiner
            game_screen: Surface du jeu à afficher derrière le rideau (optionnel)
        """
        if self.curtain_transition:
            # Pendant la transition rideau, d'abord dessiner le jeu en arrière-plan
            if game_screen is not None:
                screen.blit(game_screen, (0, 0))

            # Puis dessiner l'écran de chargement par-dessus avec l'effet de rideau
            self.draw_curtain_transition(screen)
        else:
            # Affichage normal de l'écran de chargement
            self.render_loading_content(screen)

    @property
    def is_complete(self):
        """Retourne True si le chargement est à 100% (avant la transition rideau)"""
        return self.progress >= 1.0

